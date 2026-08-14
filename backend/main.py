from fastapi import FastAPI,UploadFile,File
from fastapi import BackgroundTasks
from pydantic import BaseModel
from graph.workflow import build_graph
from book_rag.vector_store import BuildVectorStore
from database.query import save_message,get_messages,get_user_by_email,create_user,create_session
import os

app=FastAPI()

graph = None
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
def startup():
    global graph
    graph = build_graph()
    print("✅ LangGraph initialized successfully")

class QueryRequest(BaseModel):
    query: str
    user_id: str
    session_id: str

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class CreateSessionRequest(BaseModel):
    user_id: str
    title: str = "New Chat"

def build_vectorstore_task(file_path: str):
    BuildVectorStore(zip_path=file_path).build()


@app.get("/home")
def home():
    return {"message": "Welcome to the SynapTome"}

@app.post("/upload")
async def Upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    background_tasks.add_task(build_vectorstore_task, file_path)

    return {"message": "vector store is being created"}

@app.post("/ask")
def ask_question(request: QueryRequest):
    global graph

    result = graph.invoke({
        "user_query": request.query
    })

    # Save user message
    save_message(
        request.session_id,
        request.user_id,
        "user",
        request.query
    )

    # Save assistant response
    save_message(
        request.session_id,
        request.user_id,
        "assistant",
        result.get("response_message")
    )

    return {
        "query": request.query,
        "response": result.get("response_message")
    }


@app.get("/history")
def history(session_id: str):
    return get_messages(session_id)

@app.post("/register")
def register(request:RegisterRequest):
    email = request.email
    username = request.username
    password = request.password

    user = create_user(username, email, password)

    return {
        "message": "user created",
        "user": user
    }

@app.post("/login")
def login(request:LoginRequest):
    email = request.email
    password = request.password

    user = get_user_by_email(email)

    if not user:
        return {"error": "User not found"}

    if user[3] != password:
        return {"error": "Invalid password"}

    return {
        "message": "login successful",
        "user_id": user[0],
        "username": user[1]
    }

@app.post("/create-session")
def create_chat_session(request:CreateSessionRequest):
    user_id = request.user_id
    title = request.title

    session = create_session(user_id, title)

    return {
        "message": "session created",
        "session_id": session[0],
        "title": session[1]
    }