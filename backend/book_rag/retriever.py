from book_rag.vector_store_loader import VectorStoreLoader
from graph.state import BookState


class Retriever:
    def __init__(self):
        self.vector_store = VectorStoreLoader(collection_name="your_collection_name")
        self.db = self.vector_store.load()

    def retriever(self, state: BookState):

        retriever = self.db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )

        documents = retriever.invoke(state["standard_query"])

        print("\nQUERY:", state["standard_query"])

        for i, doc in enumerate(documents):
            print(f"\nDOC {i+1}:")
            print(doc.page_content[:300])

        return {"retrieved_docs": documents}