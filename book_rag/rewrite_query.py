from graph.state import BookState
from book_rag.llm import LLM
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

class Rewrite:

    def __init__(self):
        self.llm=LLM().llm()
        prompt=PromptTemplate.from_template("""
                You are a query rewriting assistant for a Retrieval-Augmented Generation (RAG) 
                                            system used for exam preparation.
                Your job is to rewrite the user's input into a clear, optimized search query that will retrieve the most relevant textbook content.

                The system will use the retrieved content to generate:
                1. MCQ questions
                2. One-word answer questions
                3. Short answer questions
                4. Concise summarized notes

                Rules:
                1. Preserve the original meaning of the user query.
                2. Convert informal or short queries into clear academic or textbook-style keywords.
                3. Expand concepts to include related syllabus topics, definitions, and theory terms.
                4. Ensure the rewritten query helps retrieve content useful for BOTH:
                - Question generation (MCQ, one-word, short answer)
                - Notes summarization
                5. If the query is already clear, enhance it for better retrieval.
                6. Do NOT answer the question.
                7. Do NOT generate notes or questions.

                Output ONLY the rewritten query.

                User query:
                {user_query}

                Rewritten query:
                    """)
        
        self.chain=prompt|self.llm|StrOutputParser()

    def rewrite_query(self,state:BookState):

        standard_query=self.chain.invoke({"user_query":state["user_query"]})

        return {"standard_query":standard_query}

