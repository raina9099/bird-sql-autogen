# utils/database.py
import os
import sqlite3
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any

class DatabaseManager:
    def __init__(self, db_root_path: str):
        self.db_root_path = db_root_path
        self.connections = {}
        
    def get_connection(self, db_id: str, timeout: int = 10) -> sqlite3.Connection:
        """Get or create a connection to the specified database."""
        if db_id not in self.connections:
            db_path = os.path.join(self.db_root_path, db_id, f"{db_id}.sqlite")
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")
            
            self.connections[db_id] = sqlite3.connect(db_path, timeout=timeout)
            
        return self.connections[db_id]
    
    def execute_query(self, db_id: str, query: str) -> Tuple[bool, Any, Optional[str]]:
        """Execute a SQL query and return results or error message."""
        conn = self.get_connection(db_id)
        
        try:
            result = pd.read_sql_query(query, conn)
            return True, result, None
        except Exception as e:
            return False, None, str(e)
    
    def get_tables_and_columns(self, db_id: str) -> Dict[str, List[str]]:
        """Get all tables and their columns from the database."""
        conn = self.get_connection(db_id)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get columns for each table
        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [row[1] for row in cursor.fetchall()]
            schema[table] = columns
            
        return schema
    
    def get_foreign_keys(self, db_id: str) -> List[Dict[str, str]]:
        """Get foreign key relationships in the database."""
        conn = self.get_connection(db_id)
        cursor = conn.cursor()
        
        foreign_keys = []
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get foreign keys for each table
        for table in tables:
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            for fk in cursor.fetchall():
                foreign_keys.append({
                    "table": table,
                    "column": fk[3],
                    "ref_table": fk[2],
                    "ref_column": fk[4]
                })
                
        return foreign_keys
    
    def close_all(self):
        """Close all database connections."""
        for conn in self.connections.values():
            conn.close()
        self.connections = {}
