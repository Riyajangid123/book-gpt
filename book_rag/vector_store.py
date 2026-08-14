import os
import logging
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_postgres import PGVector
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class VectorStore:
    def __init__(self):
        logger.info("Initializing VectorStore...")
        
        huggingface_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        self.connection_string = os.getenv("DATABASE_URL")

        if not huggingface_api_token:
            logger.error("HUGGINGFACEHUB_API_TOKEN environment variable not found!")
            raise ValueError("HUGGINGFACEHUB_API_TOKEN environment variable not set.")
        
        if not self.connection_string:
            logger.error("DATABASE_URL environment variable not found!")
            raise ValueError("DATABASE_URL environment variable not set.")

        logger.info("Environment variables loaded. Initializing embeddings.")
        
        try:
            self.embeddings = HuggingFaceEndpointEmbeddings(
                model="sentence-transformers/all-MiniLM-L6-v2",
                api_key=huggingface_api_token 
            )
            logger.info("HuggingFace embeddings initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace embeddings: {e}")
            raise

    def load_vector_store(self):
        logger.info("Loading vector store from PostgreSQL...")

        return PGVector(
            embeddings=self.embeddings,
            collection_name="book_chunks",
            connection=self.connection_string,
        )

