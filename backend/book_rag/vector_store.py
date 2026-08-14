import os
import zipfile
import hashlib
import tempfile
import shutil
import logging

from .loader import Document_Loader  
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuildVectorStore:
    """
    Builds and manages a vector store in PostgreSQL using PGVector.
    Handles file processing, embedding, and deduplication.
    """

    def __init__(self, file_bytes: bytes, file_name: str):
        """
        Initializes with file content and connects to the database and embedding service.
        """
        logger.info("Initializing VectorStore Builder...")
        self.file_bytes = file_bytes
        self.file_name = file_name
        
        # --- Load Environment Variables ---
        self.connection_string = os.getenv("DATABASE_URL")
        huggingface_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

        if not self.connection_string or not huggingface_api_token:
            logger.error("DATABASE_URL and HUGGINGFACEHUB_API_TOKEN must be set.")
            raise ValueError("Database URL and Hugging Face API token must be set.")

        # --- Initialize Embeddings (API-based) ---
        self.embeddings = HuggingFaceInferenceAPIEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            api_key=huggingface_api_token
        )
        logger.info("HuggingFace embeddings interface initialized successfully.")

    def _get_file_hash(self) -> str:
        """Creates a unique MD5 hash from the raw file bytes."""
        hasher = hashlib.md5()
        hasher.update(self.file_bytes)
        return hasher.hexdigest()

    def _collection_exists(self, collection_name: str) -> bool:
        """Checks if a collection with the given hash already exists in PGVector."""
        try:
            engine = create_engine(self.connection_string)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Query the exact table LangChain PGVector uses to store metadata
            query = text("SELECT * FROM langchain_pg_collection WHERE name = :name")
            result = session.execute(query, {"name": collection_name})
            exists = result.fetchone() is not None
            
            session.close()
            return exists
        except Exception as e:
            logger.error(f"Error checking for collection existence: {e}")
            return False 

    def _load_documents_safely(self):
        """
        Safely writes the file to a temporary directory, extracts if it's a ZIP, 
        loads PDFs using the Document_Loader, and then deletes the temp files.
        """
        logger.info("📚 Processing documents via secure temporary storage...")
        loader = Document_Loader()
        docs = []
        
        # Create a temporary directory that will automatically be cleaned up
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, self.file_name)

        try:
            # 1. Write the uploaded bytes to the temp file
            with open(temp_file_path, "wb") as f:
                f.write(self.file_bytes)

            # 2. Process based on file type
            if self.file_name.lower().endswith(".zip"):
                logger.info("📦 Extracting ZIP file in temp directory...")
                extract_dir = os.path.join(temp_dir, "extracted")
                os.makedirs(extract_dir, exist_ok=True)
                
                with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)

                # Find and load all PDFs inside the extracted folder
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        if file.lower().endswith(".pdf"):
                            pdf_path = os.path.join(root, file)
                            logger.info(f"Loading extracted PDF: {pdf_path}")
                            docs.extend(loader.load(pdf_path))

            elif self.file_name.lower().endswith(".pdf"):
                logger.info("Loading single PDF file...")
                docs = loader.load(temp_file_path)

            else:
                raise ValueError("Unsupported file type. Only PDF and ZIP are allowed.")
                
        finally:
            # 3. Clean up! Delete the temporary directory and all files inside it
            shutil.rmtree(temp_dir)
            logger.info("🧹 Temporary files cleaned up.")
        
        logger.info(f"✅ Total pages loaded: {len(docs)}")
        return docs

    def build(self) -> str:
        """
        The main method. Checks for existing vector store and builds a new one if needed.
        Returns the unique collection name (file hash).
        """
        collection_name = self._get_file_hash()
        
        # 1. Check if the vector store for this file already exists in the database
        if self._collection_exists(collection_name):
            logger.info(f"✅ Vector store '{collection_name}' already exists. Skipping build.")
            return collection_name
        
        logger.info(f"Vector store for '{collection_name}' not found. Starting build process.")
        
        # 2. Load documents securely using temp storage
        docs = self._load_documents_safely()
        if not docs:
            raise ValueError("No documents could be loaded from the provided file.")

        # 3. Split documents into smaller chunks
        logger.info("Splitting documents into chunks...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)

        # 4. Create embeddings and save them to PGVector
        logger.info(f"Creating embeddings and persisting {len(chunks)} chunks to PGVector...")
        PGVector.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=collection_name,
            connection=self.connection_string,
        )

        logger.info("✅ Vector store built and saved to PostgreSQL successfully!")
        return collection_name
