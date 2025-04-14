# utils/schema.py
import os
import json
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any

class SchemaManager:
    def __init__(self, db_root_path: str):
        self.db_root_path = db_root_path
        self.schema_cache = {}
        
    def get_schema_description(self, db_id: str) -> Dict[str, Any]:
        """Get the schema description for a database."""
        if db_id in self.schema_cache:
            return self.schema_cache[db_id]
        
        # Path to the database description folder
        desc_path = os.path.join(self.db_root_path, db_id, "database_description")
        
        if not os.path.exists(desc_path):
            raise FileNotFoundError(f"Database description not found: {desc_path}")
        
        # Read all CSV files in the description folder
        tables = {}
        for file in os.listdir(desc_path):
            if file.endswith(".csv"):
                table_name = file[:-4]  # Remove .csv extension
                file_path = os.path.join(desc_path, file)
                
                # Read the CSV file
                df = pd.read_csv(file_path)
                
                # Get column descriptions and sample values
                columns = []
                # for col in df.columns:
                #     # Get non-null sample values
                #     sample_values = df[col].dropna().head(5).tolist()
                    
                #     columns.append({
                #         "name": col,
                #         "sample_values": sample_values
                #     })
                df = df.fillna("")
                for idx, row in df.iterrows(): # Details of a column of the table
                    columns.append(row.to_dict())
                
                tables[table_name] = {
                    "columns": columns,
                    # "row_count": len(df)
                }
        
        # Cache the schema description
        self.schema_cache[db_id] = {
            "tables": tables
        }
        
        return self.schema_cache[db_id]
    
    def format_schema_for_prompt(self, db_id: str, selected_tables: Optional[List[str]] = None) -> str:
        """Format the schema description for use in a prompt."""
        schema = self.get_schema_description(db_id)

        # print(f"schema description\n {schema}")
        
        # Filter tables if selected_tables is provided
        # tables id a dict { tablename1: { columns: []}, tablename2: {...}, ...}
        tables = schema["tables"]
        if selected_tables:
            tables = {k: v for k, v in tables.items() if k in selected_tables}
        
        # Format the schema as a string
        schema_str = "Database Schema:\n"

        for table_name, table_info in tables.items():
            schema_str += f"Table: {table_name}\n"
            
            for col in table_info["columns"]:
                # sample_str = ", ".join([str(v) for v in col["sample_values"][:3]])
                schema_str += f"\n\tColumn Name: {col['original_column_name']}\n\tColumn Data Type: {col['data_format']}\n"

                if len(col['column_description']) > 0:
                    schema_str += f"\tColumn Description: {col['column_description']}\n"
                if len(col['value_description']) > 0:
                    schema_str += f"\tColumn Value Description: {col['value_description']}\n"
            
            schema_str += "\n"
        
        # for table_name, table_info in tables.items():
        #     schema_str += f"Table: {table_name} (Rows: {table_info['row_count']})\n"
            
        #     for col in table_info["columns"]:
        #         sample_str = ", ".join([str(v) for v in col["sample_values"][:3]])
        #         schema_str += f"  - {col['name']} (Examples: {sample_str})\n"
            
        #     schema_str += "\n"
        # print(f"schema_str\n{schema_str}")
        return schema_str
