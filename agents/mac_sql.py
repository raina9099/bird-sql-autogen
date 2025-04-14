# # agents/mac_sql.py

# from typing import Dict, List, Tuple, Optional, Any
# from .schema_selector import SchemaSelector
# from .decomposer import Decomposer
# from .sql_generator import SQLGenerator
# from .refiner import Refiner

# class MACSQL:
#     def __init__(self, config_list, schema_manager, db_manager):
#         self.schema_manager = schema_manager
#         self.db_manager = db_manager
        
#         # Initialize agents
#         self.selector = SchemaSelector(config_list, schema_manager)
#         self.decomposer = Decomposer(config_list)
#         self.sql_generator = SQLGenerator(config_list)
#         self.refiner = Refiner(config_list, db_manager)
        
#         # Maximum number of refinement attempts
#         self.max_refine_attempts = 3
    
#     def process_question(self, question: str, evidence: str, db_id: str) -> str:
#         """Process a natural language question and return a SQL query."""
#         # Step 1: Select relevant tables
#         selected_tables = self.selector.select_tables(question, evidence, db_id)
        
#         # Get the schema for selected tables
#         schema_str = self.schema_manager.format_schema_for_prompt(db_id, selected_tables)
        
#         # Step 2: Decompose the question if needed
#         decomposition = self.decomposer.decompose_question(question, evidence, schema_str)
        
#         # Step 3: Generate SQL query
#         sql_query = self.sql_generator.generate_sql(question, evidence, schema_str, decomposition)
        
#         # Step 4: Refine the SQL query if needed
#         refine_attempts = 0
#         while refine_attempts < self.max_refine_attempts:
#             # Try to execute the query
#             success, result, _ = self.db_manager.execute_query(db_id, sql_query)
            
#             if success and not result.empty:
#                 # Query executed successfully and returned results
#                 break
            
#             # Refine the query
#             refined_sql = self.refiner.refine_sql(question, evidence, schema_str, sql_query, db_id)
            
#             if refined_sql == sql_query:
#                 # No changes were made, stop refinement
#                 break
            
#             sql_query = refined_sql
#             refine_attempts += 1
        
#         return sql_query
