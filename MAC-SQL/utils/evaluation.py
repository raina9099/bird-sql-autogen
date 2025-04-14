# utils/evaluation.py
import os
import json
from typing import Dict, List, Any

def read_mini_dev_dataset(json_path: str) -> List[Dict[str, Any]]:
    """Read the mini_dev dataset from a JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# def read_gold_sql(sql_path: str) -> Dict[str, str]:
#     """Read the gold SQL queries from a file."""
#     gold_sqls = {}
    
#     with open(sql_path, 'r', encoding='utf-8') as f:
#         current_id = None
#         current_sql = []
        
#         for line in f:
#             line = line.strip()
            
#             if line.startswith("--"):
#                 # This is a comment line with the ID
#                 if current_id and current_sql:
#                     gold_sqls[current_id] = "\n".join(current_sql)
#                     current_sql = []
                
#                 current_id = line[2:].strip()
#             elif line and current_id:
#                 current_sql.append(line)
        
#         # Add the last SQL
#         if current_id and current_sql:
#             gold_sqls[current_id] = "\n".join(current_sql)
    
#     return gold_sqls
