# 📚 BookGPT — Multi-Agent RAG System for Interactive Learning

> Upload a book (PDF/ZIP). Ask it questions, generate MCQs, or get exam-ready notes — powered by a LangGraph-orchestrated multi-agent RAG pipeline.

## Overview

I built BookGPT to turn any book into an interactive study assistant. Instead of throwing everything at one giant prompt, the system is modeled as a **LangGraph state machine** — a query flows through a pipeline of specialized nodes (query rewriting, semantic retrieval, and task-specific generation) with an explicit router deciding which path to take based on what the user actually asked for.

The goal was to practice real agentic system design: retrieval-augmented generation grounded in the user's own uploaded content, stateful multi-node orchestration, and a full-stack app (FastAPI + Streamlit) wrapped in Docker for deployment.

## Features

- **Book upload (PDF or ZIP of PDFs)** — parsed with PyMuPDF and chunked for retrieval
- **LangGraph multi-agent pipeline** — a `StateGraph` routes each query through rewrite → retrieve → context-building → the right generation node
- **Intent-based router** — detects from the query whether the user wants notes, MCQs, short answers, or a general answer, and even parses "how many questions" from natural language (e.g. *"give me 10 mcqs on photosynthesis"*)
- **Query rewrite agent** — reformulates casual queries into textbook-style search queries before retrieval, to improve recall
- **Semantic retrieval with ChromaDB** — HuggingFace `all-MiniLM-L6-v2` embeddings power similarity search over the book's content
- **MCQ generation** — board-exam-style multiple-choice questions with an answer key, generated strictly from retrieved context
- **Notes generation** — condenses retrieved context into structured, bullet-point revision notes
- **Short-answer question generation** — conceptual, reasoning-based exam questions, not copy/paraphrase from the text
- **General Q&A** — answers open-ended questions grounded in the book's content, with an Answer / Key Points / Summary format
- **User auth & chat sessions** — register/login and per-session chat history, backed by PostgreSQL
- **Per-book vector store caching** — each upload is hashed (MD5); re-uploading the same book reuses the existing ChromaDB store instead of rebuilding it
- **Dockerized** — one container runs both the FastAPI API and the Streamlit UI

## Architecture

The core is a **LangGraph `StateGraph`** built around a shared `BookState`. Every query flows through the same graph, and a conditional edge after context-building decides which specialized node generates the response.

Streamlit UI (auth, upload, chat)
                        │
                        ▼
              FastAPI (/upload /ask /login
               /register /history)
                        │
                        ▼
    LangGraph workflow:
    START → router → rewrite → retrieve → context
                                    │
                    ┌───────┬───────┼───────┐
                   notes    mcq    short    qna
                    │        │       │       │
                    └────────┴───────┴───────┘
                             END
                        │
                        ▼
         ChromaDB (per-book vector store,
              MD5-hash cached)

**Node-by-node flow:**
1. **`router`** — scans the raw query for keywords (`notes` / `mcq` / `short`) and extracts a question count if present; defaults to general Q&A otherwise
2. **`rewrite`** — an LLM agent rewrites the query into a clearer, textbook-style search query, without answering it
3. **`retrieve`** — runs a top-5 similarity search against the book's ChromaDB collection using the rewritten query
4. **`context`** — concatenates the retrieved chunks into a single context block
5. **conditional branch** — routes to exactly one of `notes`, `mcq`, `short`, or `generate` (Q&A) based on `task_type`
6. each terminal node returns a `response_message`, which FastAPI sends back to the UI and logs to chat history

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend / API | FastAPI |
| Agent orchestration | LangGraph (`StateGraph`, conditional edges, shared state) |
| LLM | Groq — `llama-3.3-70b-versatile` (via `langchain-groq`) |
| Embeddings | HuggingFace `sentence-transformers/all-MiniLM-L6-v2` |
| Vector database | ChromaDB (persisted per book, MD5-hash cached) |
| Document parsing | PyMuPDF (`langchain_community.PyMuPDFLoader`) |
| Chunking | LangChain `RecursiveCharacterTextSplitter` (1000/200) |
| Auth & chat history | PostgreSQL (`psycopg2`) |
| Containerization | Docker |
| Language | Python 3.11 |

## Installation & Setup

**Prerequisites:** Python 3.11+, a [Groq API key](https://console.groq.com/), a PostgreSQL instance.

```bash
# 1. Clone the repo
git clone https://github.com/Riyajangid123/book-gpt.git
cd book-gpt

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the project root:

Run the backend and frontend:
```bash
# Backend
uvicorn main:app --reload --port 8000

# Frontend (in a separate terminal)
streamlit run app.py
```

The UI runs at `http://localhost:8501`, the API at `http://localhost:8000`.

**Or with Docker:**
```bash
docker build -t bookgpt .
docker run -p 7860:7860 --env-file .env bookgpt
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload a book (PDF or ZIP); vector store builds in the background |
| POST | `/ask` | Send a query; routed through the LangGraph pipeline |
| GET | `/history` | Get chat history for a session |
| POST | `/register` | Register a new user |
| POST | `/login` | Authenticate a user |
| POST | `/create-session` | Start a new chat session |

Interactive docs available at `http://localhost:8000/docs`.

Example:
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "generate 5 mcqs on photosynthesis", "user_id": "1", "session_id": "1"}'
```
The router detects `"mcq"` and `"5"` in the query, so the graph routes through the MCQ node and returns 5 board-exam-style questions with an answer key.

## Why LangGraph instead of one big prompt?

Cramming query rewriting, retrieval, and four different output formats into a single prompt tends to produce unfocused, inconsistent results. Modeling the pipeline as a graph of specialized agent nodes gives:

- **Predictable execution** — you can trace exactly which node ran and why, via `task_type` in shared state
- **Focused prompts per task** — the MCQ node's prompt is tuned only for MCQ formatting; the notes node's is tuned only for revision-style summarization
- **Easy extensibility** — adding a new capability means adding one node and one edge, not rewriting a giant prompt
- **Grounded answers** — every generation node only sees retrieved context, which keeps it from hallucinating outside the book's content

## Roadmap

- [ ] Difficulty-level tagging for MCQs (easy/medium/hard)
- [ ] Export notes and MCQs to PDF/DOCX
- [ ] Multi-book support with cross-referencing
- [ ] Streaming responses in the Streamlit UI
- [ ] Configurable multi-provider LLM layer

## Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch and open a Pull Request

## Author

**Riya Jangid** — [@Riyajangid123](https://github.com/Riyajangid123)

---
⭐ If you found this project interesting, consider giving it a star!