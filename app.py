import streamlit as st
import requests

import streamlit as st
import subprocess
import time
import socket

# Function to check if the backend is already running
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

# Start the FastAPI backend automatically in the background
@st.cache_resource
def start_backend():
    port = 8000
    if not is_port_in_use(port):
        # Starts uvicorn silently in the background
        subprocess.Popen([
            "uvicorn", "backend.main:app", 
            "--host", "127.0.0.1", 
            "--port", str(port)
        ])
        time.sleep(3) # Give the backend 3 seconds to boot up
    return f"http://127.0.0.1:{port}"

# Initialize backend and get the URL
BACKEND_API_URL = start_backend()

st.title("BookGPT")


if "page" not in st.session_state:
    st.session_state.page = "auth"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if st.session_state.page == "auth":


    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        email = st.text_input("Login Email")
        password = st.text_input("Login Password", type="password")

        if st.button("Login"):
            response = requests.post("http://127.0.0.1:8000/login", json={
                "email": email,
                "password": password
            })

            data = response.json()

            if "user_id" in data:
                st.session_state.user_id = data["user_id"]

                res = requests.post("http://127.0.0.1:8000/create-session", json={
                    "user_id": st.session_state.user_id,
                    "title": "New Chat"
                })

                st.session_state.session_id = res.json()["session_id"]

                st.session_state.page = "chat"

                st.success("Logged in!")
                st.rerun()
                

    with tab2:
        email_r = st.text_input("Register Email")
        username_r = st.text_input("Username")
        password_r = st.text_input("Password", type="password")

        if st.button("Register"):
            response = requests.post("http://127.0.0.1:8000/register", json={
                "email": email_r,
                "username": username_r,
                "password": password_r
            })

            st.success("Registered successfully!")

elif st.session_state.page == "chat":

    st.sidebar.title("💬 Chats")

    if st.sidebar.button("Logout"):
        st.session_state.page = "auth"
        st.session_state.user_id = None
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()


    uploaded_file = st.sidebar.file_uploader(
        "📂 Upload Book (PDF / Text)",
        type=["pdf","zip"]
    )

    st.sidebar.info("📌 Upload book to enable MCQ + exam mode questions")

    try:

        if uploaded_file is not None:
            if st.sidebar.button("Upload & Process"):
                with st.spinner("Uploading and processing book..."):

                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}

                    response = requests.post(
                        "http://127.0.0.1:8000/upload",
                        files=files
                    )

                    if response.status_code == 200:
                        st.sidebar.success("Book uploaded! Vector DB is being created.")
                    else:
                        st.sidebar.error("Upload failed.")

    except Exception as e:
        st.error("Please upload a book first")

                

    if st.sidebar.button("➕ New Chat"):
        st.session_state.messages = []

        res = requests.post("http://127.0.0.1:8000/create-session", json={
            "user_id": st.session_state.user_id,
            "title": "New Chat"
        })

        st.session_state.session_id = res.json()["session_id"]
        st.rerun()


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
                
    prompt = st.chat_input("Ask a question...")
    
    if prompt and st.session_state.session_id:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.spinner("Thinking... 📚"):
            response = requests.post(
                "http://127.0.0.1:8000/ask",
                json={
                    "query": prompt,
                    "user_id": st.session_state.user_id,
                    "session_id": st.session_state.session_id
                }
            )

        data = response.json()

        answer = data.get("response", "No response from server")


        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.rerun()