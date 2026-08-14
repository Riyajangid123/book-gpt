from graph.state import BookState
from book_rag.llm import LLM
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()

class Generate:
    def __init__(self):
        self.llm=LLM().llm()

        prompt = ChatPromptTemplate.from_template("""
            You are an expert educational tutor.

            You are given:
            1. A student's question
            2. Relevant textbook content

            Your task is to answer the student's question using ONLY the provided content.

            RULES:
            - Use only information from the context.
            - Do not use external knowledge.
            - Do not invent information.
            - If the answer cannot be found in the context, respond:
            "The provided content does not contain enough information to answer this question."
            - Explain concepts clearly and simply.
            - Use bullet points when appropriate.
            - Keep the answer exam-friendly and easy to understand.

            CONTEXT:
            {context}

            QUESTION:
            {user_query}

            Provide:

            ### Answer
            A detailed explanation.

            ### Key Points
            - Important point 1
            - Important point 2
            - Important point 3

            ### Summary
            A short 2-3 sentence summary.

            ANSWER:
            """)
        
        self.chain=prompt|self.llm
    
    def generate_answer(self,state:BookState):

        response=self.chain.invoke({"user_query":state["user_query"],"context":state["context"]})

        return {"response_message":response.content}