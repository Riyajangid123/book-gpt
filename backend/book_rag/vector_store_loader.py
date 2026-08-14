import os
from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEndpointEmbeddings

class VectorStoreLoader:
    """
    Connects to and loads an existing PGVector store for retrieval.
    """
    def __init__(self, collection_name: str):
        """
        Initializes the loader with the specific collection to target.

        Args:
            collection_name: The unique hash of the file to retrieve from.
        """
        self.collection_name = collection_name
        self.connection_string = os.getenv("DATABASE_URL")
        huggingface_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

        if not self.connection_string or not huggingface_api_token:
            raise ValueError("Database URL and Hugging Face API token must be set.")

        self.embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=huggingface_api_token
        )

    def load(self) -> PGVector:
        """
        Initializes and returns the PGVector store object.
        """
        store = PGVector(
            collection_name=self.collection_name,
            connection=self.connection_string,
            embeddings=self.embeddings,
        )
        return store
