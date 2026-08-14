from graph.state import BookState

def context_node(state:BookState):
        docs = state["retrieved_docs"]

        context = "\n\n".join([doc.page_content for doc in docs])

        return {"context": context}