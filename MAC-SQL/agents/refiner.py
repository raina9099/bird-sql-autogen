# agents/refiner.py

from typing import Dict, List, Tuple, Optional, Any
import autogen
import re

class Refiner:
    def __init__(self, config_list, db_manager):
        self.db_manager = db_manager
        self.agent = autogen.AssistantAgent(
            name="Refiner",
            llm_config={
                "config_list": config_list,
                "temperature": 0.1,
            },
            code_execution_config=False,
            system_message="""You are a database expert that specializes in fixing SQL queries.

                Your task is to analyze SQL execution errors and fix the SQL query to make it work correctly.

                You should follow these guidelines:
                1. Carefully analyze the error message to understand what went wrong.
                2. Check for syntax errors, invalid column or table names, and logical errors.
                3. Make sure your fixed SQL query is syntactically correct and executable.
                4. Preserve the original intent of the query while fixing the issues.
                5. Always format your SQL query properly for readability.

                Output your fixed SQL query in the following format:

                [your fixed SQL query here]

                Explain your changes and reasoning before providing the fixed SQL query.
            """
        )

    def refine_sql(self, question: str, evidence: str, schema_str: str, 
                  sql_query: str, db_id: str) -> str:
        """Refine a SQL query based on execution errors."""
        # Try to execute the SQL query
        success, result, error_msg = self.db_manager.execute_query(db_id, sql_query)
        
        if success:
            # If the query executed successfully, check if the result is empty
            if result.empty:
                # Create a user agent for this interaction
                user_proxy = autogen.UserProxyAgent(
                    name="User",
                    human_input_mode="NEVER",
                    max_consecutive_auto_reply=0,
                    code_execution_config=False,
                )
                
                # Prepare the message for empty result
                message = f"""Question: {question}
                    Evidence: {evidence}
                    Database Schema:
                    {schema_str}

                    SQL Query:
                    {sql_query}

                    The SQL query executed successfully but returned an empty result. Please review the query and make adjustments if needed to ensure it returns the expected data.
                """
                
                # Initiate the conversation
                user_proxy.initiate_chat(
                    self.agent,
                    message=message,
                )
                
                # Extract the fixed SQL query from the response
                response = self.agent.last_message(user_proxy)["content"]
                fixed_sql = self._extract_sql_from_response(response)
                
                if fixed_sql:
                    return fixed_sql
                
                # If the result is not empty or no fixed SQL was provided, return the original query
                return sql_query
            else:
                # If the query executed successfully and returned results, return the original query
                return sql_query
        else:
            # If the query failed, create a user agent for this interaction
            user_proxy = autogen.UserProxyAgent(
                name="User",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0,
                code_execution_config=False,
            )
            
            # Prepare the message for error
            message = f"""Question: {question}
                Evidence: {evidence}
                Database Schema:
                {schema_str}

                SQL Query:
                {sql_query}

                Error Message:
                {error_msg}

                Please fix the SQL query to address the error.
            """
            
            # Initiate the conversation
            user_proxy.initiate_chat(
                self.agent,
                message=message,
            )
            
            # Extract the fixed SQL query from the response
            # response = self.agent.last_message()["content"]
            response = self.agent.last_message(user_proxy)["content"]
            fixed_sql = self._extract_sql_from_response(response)
            
            if fixed_sql:
                return fixed_sql
            else:
                # If no fixed SQL was provided, return the original query
                return sql_query
    
    def _extract_sql_from_response(self, response: str) -> Optional[str]:
        """Extract SQL query from the agent's response."""
        # print(f"response\n{response}")
        # Try to extract SQL query from markdown code blocks with ```
        sql_blocks = re.findall(r"```sql\s*(.*?)\s*```", response, re.DOTALL) 
        if len(sql_blocks) > 0:
            return sql_blocks[0].strip()
        
        # Try to extract SQL query from generic markdown code blocks
        sql_blocks = re.findall(r"```\s*(SELECT.*?)\s*```", response, re.DOTALL)
        if len(sql_blocks) > 0:
            return sql_blocks[0].strip()
        
        # Try to extract SQL query directly from the response
        # sql_match = re.search(r"(?:SELECT|WITH|CREATE|INSERT|UPDATE|DELETE).*?;", response, re.DOTALL | re.IGNORECASE)
        # if sql_match:
        #     return sql_match.group(0).strip()
        
        # If no SQL query is found, look for lines starting with SELECT
        lines = response.split("\n")
        sql_lines = []
        in_sql = False
        
        for line in lines:
            line_stripped = line.strip()
            # Start collecting SQL when we see a SELECT statement
            if re.match(r"^SELECT", line_stripped, re.IGNORECASE):
                in_sql = True
                sql_lines.append(line_stripped)
            # Continue collecting SQL lines
            elif in_sql and line_stripped:
                sql_lines.append(line_stripped)
                # Stop collecting if we reach a semicolon
                if line_stripped.endswith(';'):
                    break
        
        if sql_lines:
            return " ".join(sql_lines)
        
        return None

