import os
import requests
import streamlit as st

BACKEND_API_URL = os.getenv(
    "BACKEND_API_URL",
    "http://127.0.0.1:8000"   
)

st.set_page_config(page_title="SynapTome", page_icon="🧠", layout="centered")
st.title("🧠 SynapTome")


if "page" not in st.session_state:
    st.session_state.page = "auth"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "session_id" not in st.session_state:
    st.session_state.session_id = None

# --- AUTHENTICATION PAGE ---
if st.session_state.page == "auth":
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        email = st.text_input("Login Email", key="login_email")
        password = st.text_input("Login Password", type="password", key="login_pass")

        if st.button("Login", use_container_width=True):
            try:
                response = requests.post(
                    f"{BACKEND_API_URL}/login", 
                    json={"email": email, "password": password},
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    if "user_id" in data:
                        st.session_state.user_id = data["user_id"]

                        res = requests.post(
                            f"{BACKEND_API_URL}/create-session", 
                            json={"user_id": st.session_state.user_id, "title": "New Chat"},
                            timeout=10
                        )
                        st.session_state.session_id = res.json()["session_id"]
                        st.session_state.page = "chat"
                        st.success("Successfully logged in!")
                        st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("⚠️ Unable to connect to the backend server. It might be waking up from sleep mode on Render. Please wait 30 seconds and try again.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

    with tab2:
        email_r = st.text_input("Register Email", key="reg_email")
        username_r = st.text_input("Username", key="reg_user")
        password_r = st.text_input("Password", type="password", key="reg_pass")

        if st.button("Register", use_container_width=True):
            try:
                response = requests.post(
                    f"{BACKEND_API_URL}/register", 
                    json={"email": email_r, "username": username_r, "password": password_r},
                    timeout=15
                )
                if response.status_code == 200 or response.status_code == 201:
                    st.success("Registered successfully! You can now switch to the Login tab.")
                else:
                    st.error("Registration failed. Email might already be taken.")
            except requests.exceptions.ConnectionError:
                st.error("⚠️ Backend server is currently starting up on Render. Please wait a moment.")

# --- CHAT INTERFACE PAGE ---
elif st.session_state.page == "chat":
    st.sidebar.title("💬 Chats")

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.page = "auth"
        st.session_state.user_id = None
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

    uploaded_file = st.sidebar.file_uploader(
        "📂 Upload Book (PDF)",
        type=["pdf","zip"]  
    )

    st.sidebar.info("📌 Upload a book to build your vector database for asking questions.")


    if uploaded_file is not None:
        if st.sidebar.button("Upload & Process", use_container_width=True):
            with st.spinner("Processing document... (May take a minute)"):
                
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                data = {"user_id": st.session_state.user_id} 

                try:
                    response = requests.post(
                        f"{BACKEND_API_URL}/upload",
                        files=files,
                        data=data, 
                        timeout=180 
                    )

                    if response.status_code == 200:
                        response_data = response.json()
                        st.sidebar.success("✅ Book is processing in the background!")
                
                        st.session_state['current_collection'] = response_data.get("collection_name")
                    else:
                        st.sidebar.error(f"Upload failed: {response.text}")
                
                except requests.exceptions.RequestException as e:
                    st.sidebar.error(f"Connection Error: {e}")


    if st.sidebar.button("➕ New Chat", use_container_width=True):
        try:
            st.session_state.messages = []
            res = requests.post(
                f"{BACKEND_API_URL}/create-session", 
                json={"user_id": st.session_state.user_id, "title": "New Chat"},
                timeout=10
            )
            st.session_state.session_id = res.json()["session_id"]
            st.rerun()
        except Exception as e:
            st.error("Failed to start a new chat session.")

    # Render previous messages in the chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input for new prompt
    prompt = st.chat_input("Ask a question about your uploaded book...")

    if prompt and st.session_state.session_id:
        if 'current_collection' not in st.session_state or st.session_state['current_collection'] is None:
            st.error("Please upload and process a book before asking questions.")
        else:
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("Analyzing text... 📚"):
                    try:
                        json_payload = {
                            "query": prompt,
                            "user_id": st.session_state.user_id,
                            "session_id": st.session_state.session_id,
                            "collection_name": st.session_state.get('current_collection')
                        }
                        
                        response = requests.post(
                            f"{BACKEND_API_URL}/ask",
                            json=json_payload,
                            timeout=60 
                        )

                        if response.status_code == 200:
                            data = response.json()
                            answer = data.get("response", "No response from server")
                        else:
                            answer = f"⚠️ Backend Error: {response.status_code} - {response.text}"
                    
                    except Exception as e:
                        answer = f"⚠️ Connection Error: Failed to reach the backend. ({e})"
                
                message_placeholder.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
