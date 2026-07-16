from book_rag.llm import LLM
from graph.state import BookState
from langchain_core.prompts import ChatPromptTemplate


class ShortAnswerNode:
    def __init__(self):
        self.llm = LLM().llm()

        SYSTEM_PROMPT = """
            You are an expert CBSE/NCERT exam question setter.

            Your task:
            - Generate HIGH QUALITY exam questions from the given content
            - Do NOT copy sentences from text
            - Do NOT create direct factual paraphrasing questions
            - Focus on conceptual understanding, application, and reasoning

            Rules:
            1. Questions must test understanding, not memory
            2. Avoid direct line-based questions from the book
            3. Use NCERT syllabus but reframe creatively
            4. Include real exam patterns (assertion-reason, scenario-based, application)
            5. Make distractors conceptually close
            6. Do NOT include answer key unless asked
            """

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{user_query}")
            ])


        self.chain = prompt | self.llm

    def run(self, state: BookState):
        response = self.chain.invoke({
            "user_query": state["user_query"]
        })

        return {"response_message": response.content}