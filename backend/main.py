import hashlib
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Form
from pydantic import BaseModel
import os
import shutil
import tempfile
import hashlib
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

def build_vectorstore_task(user_id: str, temp_file_path: str, original_filename: str):
    """
    This background task now works with a file path instead of raw bytes.
    """
    try:
        print(f"Background task started for file: {original_filename} from user: {user_id}")
        # Open and read the file from the temporary path
        with open(temp_file_path, "rb") as f:
            file_bytes = f.read()

        builder = BuildVectorStore(file_bytes=file_bytes, file_name=original_filename)
        collection_name = builder.build()
        
        # Link the book to the user in the database
        add_user_book(user_id=user_id, book_title=original_filename, collection_name=collection_name)
        
        print(f"Background task finished. Collection '{collection_name}' is ready and linked.")
    
    except Exception as e:
        print(f"Error in background task for {original_filename}: {e}")
    
    finally:
        # CRUCIAL: Clean up the temporary file after processing
        os.remove(temp_file_path)
        print(f"Temporary file {temp_file_path} deleted.")

# --- API Endpoints ---

@app.post("/upload")
async def upload_book(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Handles large file uploads by streaming them to a temporary file on disk
    to avoid memory overflow.
    """
    try:
        # Create a temporary file to save the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            # Stream the file content in chunks to the temporary file
            shutil.copyfileobj(file.file, tmp)
            temp_file_path = tmp.name

        # Now, read the small file back to get its hash for the immediate response
        with open(temp_file_path, "rb") as f:
            file_bytes_for_hash = f.read()
        
        hasher = hashlib.md5()
        hasher.update(file_bytes_for_hash)
        collection_name = hasher.hexdigest()

        # Pass the FILE PATH to the background task, not the file content
        background_tasks.add_task(build_vectorstore_task, user_id, temp_file_path, file.filename)

        return {
            "message": "File upload successful. Processing has started.",
            "collection_name": collection_name
        }
    finally:
        await file.close()

@app.get("/")
def home():
    return {"message": "Welcome to the SynapTome"}

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
