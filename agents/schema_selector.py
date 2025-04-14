# agents/schema_selector.py

from typing import Dict, List, Tuple, Optional, Any
import autogen

class SchemaSelector:
    def __init__(self, config_list, schema_manager):
        self.schema_manager = schema_manager
        self.agent = autogen.AssistantAgent(
            name="SchemaSelector",
            llm_config={
                "config_list": config_list,
                "temperature": 0.2,
            },
            code_execution_config=False,
            system_message="""You are a database expert that specializes in analyzing questions and selecting the most relevant tables and columns from a database schema.

                Your task is to analyze the user's question and the database schema, then select only the tables and columns that are necessary to answer the question.

                You should be precise and avoid selecting unnecessary tables or columns.

                Output your selection in the following format:

                SELECTED TABLES: [list of table names]
            """
        )

    def select_tables(self, question: str, evidence: str, db_id: str) -> List[str]:
        """Select relevant tables for the given question."""
        # Get the full schema description
        schema_str = self.schema_manager.format_schema_for_prompt(db_id)
        
        # Create a user agent for this interaction
        user_proxy = autogen.UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )
        
        # Prepare the message
        message = f"""Question: {question}
            Evidence: {evidence}
            {schema_str}

            Analyze the question and evidence carefully, then select only the tables that are necessary to answer this question.
        """
        
        # Initiate the conversation
        user_proxy.initiate_chat(
            self.agent,
            message=message,
        )
        
        # Extract the selected tables from the response
        # response = self.agent.last_message()["content"]
        response = self.agent.last_message(user_proxy)["content"]
        selected_tables = []
        for line in response.split("\n"):
            if line.startswith("SELECTED TABLES:"):
                tables_str = line.replace("SELECTED TABLES:", "").strip()
                # Parse the table names
                if tables_str.startswith("[") and tables_str.endswith("]"):
                    tables_str = tables_str[1:-1]
                    selected_tables = [t.strip().strip("'\"") for t in tables_str.split(",")]
                break
        
        return selected_tables
