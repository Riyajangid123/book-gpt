from langchain_community.document_loaders import PyMuPDFLoader

class Document_Loader:
    def load(self,pdf_path):
        loader = PyMuPDFLoader(pdf_path)
        docs = loader.load()

        return docs