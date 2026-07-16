import os
import zipfile

from book_rag.loader import Document_Loader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import hashlib

class BuildVectorStore:

    def __init__(
        self,
        zip_path: str,
        extract_directory: str = "./extracted_book"
    ):
        self.zip_path = zip_path
        self.extract_directory = extract_directory

    def extract_zip(self):
        print("📦 Extracting ZIP...")

        with zipfile.ZipFile(self.zip_path, "r") as zip_ref:
            zip_ref.extractall(self.extract_directory)

        print("✅ ZIP extracted")

    def get_file_hash(self,file_path):
        hasher=hashlib.md5()

        with open(file_path,"rb") as f:
            while chunk:=f.read(8192):
                hasher.update(chunk)

        return hasher.hexdigest()

    def load_documents(self):
        print("📚 Loading PDFs...")

        docs = []
        loader = Document_Loader()

        for root, _, files in os.walk(self.extract_directory):

            for file in files:

                if file.lower().endswith(".pdf"):

                    pdf_path = os.path.join(root, file)

                    print(f"Loading: {pdf_path}")

                    try:
                        pdf_docs = loader.load(pdf_path)

                        print(f"Loaded {len(pdf_docs)} pages from {file}")

                        docs.extend(pdf_docs)

                    except Exception as e:
                        print(f"ERROR in {file}")
                        print(e)

        print(f"✅ Total pages loaded: {len(docs)}")

        return docs

    def build(self):

        file_hash = self.get_file_hash(self.zip_path)

        persist_directory = f"./chromadb/{file_hash}"

        if os.path.exists(persist_directory):
            print("✅ Vector store already exists")
            return persist_directory

        # ZIP file
        if self.zip_path.lower().endswith(".zip"):
            self.extract_zip()
            docs = self.load_documents()

        # Single PDF
        elif self.zip_path.lower().endswith(".pdf"):
            loader = Document_Loader()
            docs = loader.load(self.zip_path)

        else:
            raise ValueError(
                "Only PDF and ZIP files are supported"
            )

        print("Splitting documents...")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = splitter.split_documents(docs)

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory
        )

        vectorstore.persist()

        print("✅ Vector store saved successfully")

        return persist_directory