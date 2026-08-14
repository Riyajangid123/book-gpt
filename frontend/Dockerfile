FROM python:3.11-slim

WORKDIR /app

# Install basic dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Streamlit code
COPY . .

# Streamlit default port
EXPOSE 8501

# Streamlit production flags for cloud proxies and WebSockets
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]

