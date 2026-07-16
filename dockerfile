FROM python:3.11-slim

# Create a secure, non-root user (Hugging Face standard)
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Install system dependencies (needed for certain PDF parsers or vector DBs)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all code to the container
COPY --chown=user . .

# Set running environment
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Grant execution rights to startup script
RUN chmod +x start.sh

# Expose port 7860 (This is the only port Hugging Face forwards externally)
EXPOSE 7860

# Run both the API and Streamlit on startup
CMD ["./start.sh"]