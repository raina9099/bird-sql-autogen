# agents/decomposer.py

from typing import Dict, List, Tuple, Optional, Any
import autogen

class Decomposer:
    def __init__(self, config_list):
        self.agent = autogen.AssistantAgent(
            name="Decomposer",
            llm_config={
                "config_list": config_list,
                "temperature": 0.3,
            },
            code_execution_config=False,
            system_message="""You are a database expert that specializes in breaking down complex questions into simpler sub-questions.

                Your task is to analyze the user's question and decompose it into a series of simpler sub-questions that can be answered step by step.

                For each sub-question, you should also provide a clear explanation of how it contributes to answering the original question.

                Output your decomposition in the following format:

                ANALYSIS: [your analysis of the question complexity]

                [If the question is simple enough to answer directly]:
                DIRECT: The question is simple enough to answer with a single SQL query.

                [If the question needs decomposition]:
                SUB-QUESTION 1: [first sub-question]
                EXPLANATION 1: [explanation of how this sub-question helps]

                SUB-QUESTION 2: [second sub-question]
                EXPLANATION 2: [explanation of how this sub-question helps]
                ...and so on.

                FINAL APPROACH: [summary of how to combine the answers to sub-questions to answer the original question]
            """
        )

    def decompose_question(self, question: str, evidence: str, schema_str: str) -> Dict[str, Any]:
        """Decompose a complex question into simpler sub-questions."""
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
            Database Schema:
            {schema_str}

            Analyze the question and decompose it into simpler sub-questions if needed.
        """
        
        # Initiate the conversation
        user_proxy.initiate_chat(
            self.agent,
            message=message,
        )
        
        # Extract the decomposition from the response
        response = self.agent.last_message(user_proxy)["content"]
        
        # Parse the response
        result = {
            "is_direct": "DIRECT:" in response,
            "sub_questions": [],
            "explanations": [],
            "final_approach": ""
        }
        
        if not result["is_direct"]:
            lines = response.split("\n")
            current_sub_q = None
            current_exp = None
            
            for line in lines:
                line = line.strip()
                if line.startswith("SUB-QUESTION "):
                    if current_sub_q is not None and current_exp is not None:
                        result["sub_questions"].append(current_sub_q)
                        result["explanations"].append(current_exp)
                    current_sub_q = line.split(":", 1)[1].strip()
                    current_exp = None
                elif line.startswith("EXPLANATION "):
                    current_exp = line.split(":", 1)[1].strip()
                elif line.startswith("FINAL APPROACH:"):
                    result["final_approach"] = line.split(":", 1)[1].strip()
            
            # Add the last sub-question and explanation
            if current_sub_q is not None and current_exp is not None:
                result["sub_questions"].append(current_sub_q)
                result["explanations"].append(current_exp)
        
        return result
