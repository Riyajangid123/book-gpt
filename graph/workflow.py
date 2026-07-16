from graph.state import BookState
from langgraph.graph import StateGraph,START,END
from book_rag.retriever import Retriever
from book_rag.rewrite_query import Rewrite
from book_rag.generate_node import Generate
from book_rag.vector_store import VectorStore
from book_rag.loader import Document_Loader
from book_rag.notes_node import NotesNode
from book_rag.mcq_node import MCQNode
from book_rag.short_node import ShortAnswerNode
from book_rag.context import context_node
import re

import re

def router_node(state: BookState):
    query = state["user_query"].lower()

    match = re.search(r"(\d+)", query)
    num_questions = int(match.group(1)) if match else 5

    if "notes" in query:
        task_type = "notes"
    elif "mcq" in query:
        task_type = "mcq"
    elif "short" in query:
        task_type = "short"
    else:
        task_type = "all"

    return {
        "task_type": task_type,
        "num_questions": num_questions
    }
    
def route_decision(state: BookState):
    return state["task_type"]
    

def build_graph():

    graph = StateGraph(BookState)

    # nodes
    graph.add_node("router", router_node)
    graph.add_node("rewrite", Rewrite().rewrite_query)
    graph.add_node("retrieve", Retriever().retriever)

    graph.add_node("context", context_node)
    graph.add_node("notes", NotesNode().run)
    graph.add_node("mcq", MCQNode().run)
    graph.add_node("short", ShortAnswerNode().run)
    graph.add_node("generate", Generate().generate_answer)

    graph.add_edge(START, "router")
    graph.add_edge("router", "rewrite")
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("retrieve", "context")

    graph.add_conditional_edges(
        "context",
        route_decision,
        {
            "notes": "notes",
            "mcq": "mcq",
            "short": "short",
            "all": "generate"
        }
    )

    graph.add_edge("notes", END)
    graph.add_edge("mcq", END)
    graph.add_edge("short", END)
    graph.add_edge("generate", END)

    return graph.compile()