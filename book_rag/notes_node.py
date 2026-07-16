from book_rag.llm import LLM
from graph.state import BookState
from langchain_core.prompts import ChatPromptTemplate


class NotesNode:
    def __init__(self):
        self.llm = LLM().llm()

        prompt = ChatPromptTemplate.from_template("""
            You are an expert teacher creating exam revision notes.

            Use ONLY the given context.

            TASK:
            Generate concise, well-structured NOTES for students.

            RULES:
            - Use headings and bullet points
            - Highlight important keywords
            - Do NOT add external knowledge
            - Keep it easy for revision

            CONTEXT:
            {context}

            TOPIC:
            {user_query}

            FINAL NOTES:
            """)

        self.chain = prompt | self.llm

    def run(self, state: BookState):
        response = self.chain.invoke({
            "context": state["context"],
            "user_query": state["user_query"]
        })

        return {"response_message": response.content}