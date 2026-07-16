#!/bin/bash

# 1. Start the FastAPI backend on internal port 8000 in the background
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &

# 2. Start Streamlit on Hugging Face's exposed port 7860
streamlit run frontend/app.py --server.port 7860 --server.address 0.0.0.0