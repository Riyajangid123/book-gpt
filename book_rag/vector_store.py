import os

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_postgres import PGVector
import os
from dotenv import load_dotenv

load_dotenv()

class VectorStore:
    def __init__(self):
        self.embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=os.environ["HUGGINGFACEHUB_API_TOKEN"],
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.connection_string = os.environ["DATABASE_URL"] 

    def load_vector_store(self):
        return PGVector(
            embeddings=self.embeddings,
            collection_name="book_chunks",
            connection=self.connection_string,
        )