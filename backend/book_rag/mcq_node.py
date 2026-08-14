from book_rag.llm import LLM
from graph.state import BookState
from langchain_core.prompts import ChatPromptTemplate


class MCQNode:
    def __init__(self):
        self.llm = LLM().llm()

        prompt = ChatPromptTemplate.from_template("""
            Generate exam-level MCQs from NCERT content.

            Requirements:
            - Do not copy text directly
            - Use conceptual reasoning
            - Difficulty: Board exam level

            Topic/content:
            {user_query}
    
            Generate exactly {num_questions} MCQs from the provided context.

            Rules:
            1. Each MCQ must be on a NEW LINE.
            2. Leave ONE BLANK LINE between questions.
            3. Each option must be on its own line.
            4. Use exactly 4 options:
            A)
            B)
            C)
            D)
            5. Do not write options on the same line.
            6. After all questions, create a separate ANSWER KEY section.
            7. Output must be clean markdown.

            Format:

            Q1. Question text?

            A) Option 1
            B) Option 2
            C) Option 3
            D) Option 4

            Q2. Question text?

            A) Option 1
            B) Option 2
            C) Option 3
            D) Option 4

            ANSWER KEY

            Q1. B
            Q2. C

            Context:
            {context}
            """)

        self.chain = prompt | self.llm

    def run(self, state: BookState):
        response = self.chain.invoke({
            "context": state["context"],
            "num_questions": state["num_questions"]})

        return {"response_message": response.content}