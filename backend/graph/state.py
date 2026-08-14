from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class BookState(TypedDict):
    user_query: str
    standard_query: str

    task_type: Literal["notes", "mcq", "short", "all"]

    retrieved_docs: list
    num_questions: int
    context: str

    notes: str
    mcqs: str
    short_answers: str
    response_message: str