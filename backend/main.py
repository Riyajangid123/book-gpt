import hashlib
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from pydantic import BaseModel
from book_rag.vector_store import BuildVectorStore
from database.query import save_message, get_messages, get_user_by_email, create_user, create_session, add_user_book
from graph.workflow import build_graph

app = FastAPI()
graph = None

@app.on_event("startup")
def startup():
    """Initializes the LangGraph graph when the application starts."""
    global graph
    graph = build_graph()
    print("✅ LangGraph initialized successfully")

class QueryRequest(BaseModel):
    query: str
    user_id: str
    session_id: str
    collection_name: str  

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

# --- Background Task Definition ---

def build_vectorstore_task(user_id: str, file_bytes: bytes, file_name: str):
    """
    This function runs in the background to perform the heavy processing.
    It uses the BuildVectorStore class to load, chunk, embed, and save to PGVector.
    """
    try:
        print(f"Background task started for file: {file_name}")
        builder = BuildVectorStore(file_bytes=file_bytes, file_name=file_name)
        collection_name = builder.build()

        add_user_book(user_id=user_id, book_title=file_name, collection_name=collection_name)
        print(f"Background task finished. Collection '{collection_name}' is ready.")
    except Exception as e:
        print(f"Error in background task for {file_name}: {e}")

# --- API Endpoints ---

@app.get("/home")
def home():
    return {"message": "Welcome to the SynapTome"}

@app.post("/upload")
async def upload_book(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...), 
    file: UploadFile = File(...)
):
    """
    Handles file uploads:
    1. Reads the file into memory.
    2. Immediately calculates and returns the file's unique hash (collection_name).
    3. Triggers a background task to do the heavy processing.
    """
    print(f"Upload received for file: {file.filename}")
    file_bytes = await file.read()
    
    # Immediately calculate the hash to return to the user
    hasher = hashlib.md5()
    hasher.update(file_bytes)
    collection_name = hasher.hexdigest()
    
    # Queue the heavy processing to run in the background
    background_tasks.add_task(build_vectorstore_task, user_id, file_bytes, file.filename)

    # Return the unique ID right away so the frontend can use it
    return {
        "message": "File upload successful. Processing has started in the background.",
        "collection_name": collection_name
    }

@app.post("/ask")
def ask_question(request: QueryRequest):
    """Answers a question by invoking the graph for a specific book collection."""
    global graph
    
    print(f"Invoking graph for collection: {request.collection_name}")
    result = graph.invoke({
        "user_query": request.query,
        "collection_name": request.collection_name
    })
    
    response_message = result.get("response_message", "Sorry, I encountered an error.")

    # Save conversation to the database
    save_message(request.session_id, request.user_id, "user", request.query)
    save_message(request.session_id, request.user_id, "assistant", response_message)

    return {"query": request.query, "response": response_message}

@app.post("/register")
def register(request: RegisterRequest):
    user_tuple = create_user(request.username, request.email, request.password)
    return {
        "message": "User created successfully",
        "user_id": user_tuple[0],
        "username": user_tuple[1]
    }

@app.post("/login")
def login(request: LoginRequest):
    user_tuple = get_user_by_email(request.email)

    if not user_tuple:
        raise HTTPException(status_code=404, detail="User not found")

    if user_tuple[3] != request.password:
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "message": "Login successful",
        "user_id": user_tuple[0],    
        "username": user_tuple[1]  
    }

@app.post("/create-session")
def create_chat_session(request: CreateSessionRequest):
    session_tuple = create_session(request.user_id, request.title)
    return {
        "message": "Session created",
        "session_id": session_tuple[0], 
        "title": session_tuple[1]   
    }

@app.get("/history")
def history(session_id: str):
    messages = get_messages(session_id)
    return {"messages": messages}
