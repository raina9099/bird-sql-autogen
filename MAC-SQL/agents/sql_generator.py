# agents/sql_generator.py

from typing import Dict, List, Tuple, Optional, Any
import autogen
import re

class SQLGenerator:
    def __init__(self, config_list):
        self.agent = autogen.AssistantAgent(
            name="SQLGenerator",
            llm_config={
                "config_list": config_list,
                "temperature": 0.2,
            },
            code_execution_config=False,
            system_message="""You are a database expert that specializes in generating SQL queries to answer questions.

                Your task is to generate a SQL query that correctly answers the given question based on the provided database schema.

                You should follow these guidelines:
                1. Use only the tables and columns mentioned in the schema.
                2. Make sure your SQL query is syntactically correct and executable.
                3. Use appropriate joins, filters, and aggregations as needed.
                4. If the question involves multiple steps, you may need to use subqueries or CTEs.
                5. Always format your SQL query properly for readability.

                Output your SQL query in the following format:

                [your SQL query here]


                If you need to explain your approach or reasoning, do so before the SQL query.
            """
        )

    def generate_sql(self, question: str, evidence: str, schema_str: str, 
                     decomposition: Optional[Dict[str, Any]] = None) -> str:
        """Generate a SQL query for the given question."""
        # Create a user agent for this interaction
        user_proxy = autogen.UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )
        
        # Prepare the message
        if decomposition and not decomposition["is_direct"]:
            # If we have a decomposition with sub-questions, use it
            message = f"""Question: {question}
                Evidence: {evidence}
                Database Schema:
                {schema_str}

                I've broken down this question into the following sub-questions:
            """
            for i, (sub_q, exp) in enumerate(zip(decomposition["sub_questions"], decomposition["explanations"])):
                message += f"\nSub-question {i+1}: {sub_q}\nExplanation: {exp}\n"
            
            message += f"\nFinal approach: {decomposition['final_approach']}\n\nNow, please generate the SQL query that answers the original question."
        else:
            # If we don't have a decomposition or it's a direct question
            message = f"""Question: {question}
                Evidence: {evidence}
                Database Schema:
                {schema_str}

                Generate a SQL query that correctly answers this question.
            """
        
        # Initiate the conversation
        user_proxy.initiate_chat(
            self.agent,
            message=message,
        )
        
        # Extract the SQL query from the response
        response = self.agent.last_message(user_proxy)["content"]
        sql_query = ""
        
        # Extract SQL query from markdown code block
        sql_blocks = re.findall(r"``````", response, re.DOTALL)
        if sql_blocks:
            sql_query = sql_blocks[0].strip()
        else:
            # If no code block, try to extract the SQL query directly
            lines = response.split("\n")
            sql_lines = []
            in_sql = False
            
            for line in lines:
                if line.strip().upper().startswith("SELECT") or in_sql:
                    in_sql = True
                    sql_lines.append(line)
            
            if sql_lines:
                sql_query = "\n".join(sql_lines)
        
        return sql_query
