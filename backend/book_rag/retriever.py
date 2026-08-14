from book_rag.vector_store_loader import VectorStoreLoader

class Retriever:
    def retriever(self, state):
        """
        Extracts the collection_name from the current state, 
        loads that specific vector store, and searches it.
        """
        query = state.get("standard_query") 
    
        
        collection_name = state.get("collection_name")
        
        print(f"🔍 Retrieving documents for collection: {collection_name}")
        
        if not collection_name:
            raise ValueError("No collection_name provided in the state!")

        loader = VectorStoreLoader(collection_name=collection_name)
        vector_store = loader.load()
        
        # 3. Perform the search
        results = vector_store.similarity_search(query, k=5)
        
        print(f"✅ Found {len(results)} relevant document chunks.")
        
        return {"retrieved_docs": results}
