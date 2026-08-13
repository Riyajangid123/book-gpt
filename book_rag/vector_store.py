import os

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_postgres import PGVector
from dotenv import load_dotenv

load_dotenv()

class VectorStore:
    def __init__(self):
        self.embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"]
        )
        
        self.connection_string = os.environ["DATABASE_URL"] 

    def load_vector_store(self):
        return PGVector(
            embeddings=self.embeddings,
            collection_name="book_chunks",
            connection=self.connection_string,
        )