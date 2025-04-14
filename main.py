# main.py
import os
import json
import argparse
import autogen
from tqdm import tqdm

from agents.schema_selector import SchemaSelector
from agents.decomposer import Decomposer
from agents.sql_generator import SQLGenerator
from agents.refiner import Refiner
from utils.database import DatabaseManager
from utils.schema import SchemaManager
from utils.evaluation import read_mini_dev_dataset
from config import *

class MACSQL:
    def __init__(self, config_list, schema_manager, db_manager, max_refine_attempts=3):
        self.schema_manager = schema_manager
        self.db_manager = db_manager
        
        # Initialize agents
        self.selector = SchemaSelector(config_list, schema_manager)
        self.decomposer = Decomposer(config_list)
        self.sql_generator = SQLGenerator(config_list)
        self.refiner = Refiner(config_list, db_manager)
        
        # Maximum number of refinement attempts
        self.max_refine_attempts = max_refine_attempts
    
    def process_question(self, question, evidence, db_id, verbose=False):
        """Process a natural language question and return a SQL query following the MAC-SQL algorithm."""
        # Step 1: Select relevant tables (Selector agent)
        if verbose:
            print("🔍 Selecting relevant tables...")
        
        # Get the full schema description
        full_schema_str = self.schema_manager.format_schema_for_prompt(db_id)
        
        # Check if we need to simplify the database schema
        # need_simplify = len(full_schema_str.split()) > 3000  # Simple heuristic, adjust as needed
        
        # if need_simplify:
        #     selected_tables = self.selector.select_tables(question, evidence, db_id)
        #     if verbose:
        #         print(f"📋 Selected tables: {selected_tables}")
        # else:
        #     # Use all tables if simplification is not needed
        #     selected_tables = None
        #     if verbose:
        #         print("📋 Using complete schema (no simplification needed)")

        selected_tables = self.selector.select_tables(question, evidence, db_id)
        
        # Step 2: Get the schema for selected tables
        schema_str = self.schema_manager.format_schema_for_prompt(db_id, selected_tables)
        
        # Step 3: Decompose the question if needed (Decomposer agent)
        if verbose:
            print("🧩 Decomposing question...")
        decomposition = self.decomposer.decompose_question(question, evidence, schema_str)
        
        if verbose:
            if decomposition["is_direct"]:
                print("📝 Question is direct, no decomposition needed")
            else:
                print(f"📝 Decomposed into {len(decomposition['sub_questions'])} sub-questions:")
                for i, (sub_q, exp) in enumerate(zip(decomposition["sub_questions"], decomposition["explanations"])):
                    print(f"  Sub-question {i+1}: {sub_q}")
                    print(f"  Explanation: {exp}")
                print(f"  Final approach: {decomposition['final_approach']}")
        
        # Step 4: Generate SQL query (SQLGenerator agent)
        if verbose:
            print("💻 Generating SQL query...")
        sql_query = self.sql_generator.generate_sql(question, evidence, schema_str, decomposition)
        
        if verbose:
            print(f"📊 Initial SQL query:\n{sql_query}")
        
        # Step 5: Refine the SQL query if needed (Refiner agent)
        refine_attempts = 0
        while refine_attempts < self.max_refine_attempts:
            # Try to execute the query
            success, result, error_msg = self.db_manager.execute_query(db_id, sql_query)
            
            if success and not result.empty:
                # Query executed successfully and returned results
                if verbose:
                    print("✅ SQL query executed successfully!")
                    print(f"Results preview:\n{result.head()}")
                break
            
            if verbose:
                if success and result.empty:
                    print("⚠️ SQL query executed but returned empty results. Refining...")
                else:
                    print(f"❌ SQL query execution failed with error: {error_msg}. Refining...")
            
            # Refine the query
            refined_sql = self.refiner.refine_sql(question, evidence, schema_str, sql_query, db_id)
            
            if refined_sql == sql_query:
                # No changes were made, stop refinement
                if verbose:
                    print("🔄 No changes made during refinement, stopping attempts")
                break
            
            if verbose:
                print(f"🔧 Refined SQL query (attempt {refine_attempts+1}):\n{refined_sql}")
            
            sql_query = refined_sql
            refine_attempts += 1
        
        return sql_query

def main(args):
    # Initialize managers
    db_manager = DatabaseManager(SQLITE_DB_PATH)
    schema_manager = SchemaManager(SQLITE_DB_PATH)
    
    # Initialize OpenAI API configuration
    config_list = [
        {
            "model": OPENAI_MODEL,
            "api_key": OPENAI_API_KEY,
        }
    ]
    
    # Initialize MAC-SQL framework
    mac_sql = MACSQL(
        config_list=config_list,
        schema_manager=schema_manager,
        db_manager=db_manager,
        max_refine_attempts=args.max_refine_attempts
    )
    
    # Load dataset
    mini_dev_data = read_mini_dev_dataset(MINI_DEV_JSON)
    
    # Process each question
    predictions = {}
    # for item in tqdm(mini_dev_data[:args.num_samples] if args.num_samples > 0 else mini_dev_data, 
    #                  desc="Processing questions"):
    for item in tqdm(mini_dev_data[args.start: args.end+1], 
                     desc="Processing questions"):
        db_id = item["db_id"]
        question = item["question"]
        evidence = item.get("evidence", "")
        
        if args.verbose:
            print("\n" + "="*80)
            print(f"Database: {db_id}")
            print(f"Question: {question}")
            print(f"Evidence: {evidence}")
            print("="*80 + "\n")
        
        # Process the question using MAC-SQL framework
        sql_query = mac_sql.process_question(question, evidence, db_id, verbose=args.verbose)
        
        # Store prediction
        query_id = f"{db_id}/{question}"
        predictions[query_id] = sql_query
        
        if args.verbose:
            print("\n" + "-"*80)
            print(f"Final SQL: {sql_query}")
            print("-"*80 + "\n")
        
        # if args.num_samples == 1:  # If only processing one sample for debugging
        #     break

    print(f"Processed {len(predictions)} questions from index {args.start} to {args.end} (including)")
    
    # Save predictions
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(predictions, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MAC-SQL framework for Text-to-SQL")
    # parser.add_argument("--num_samples", type=int, default=-1, help="Number of samples to process (-1 for all)")
    parser.add_argument("--start", type=int, default=0, help="Index of data item to start processing from")
    parser.add_argument("--end", type=int, default=0, help="Index of data item to end processing with")
    parser.add_argument("--output", type=str, default="outputs/predictions.json", help="Output file path")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate predictions against gold SQL")
    parser.add_argument("--max_refine_attempts", type=int, default=3, help="Maximum number of SQL refinement attempts")
    
    args = parser.parse_args()
    
    main(args)
