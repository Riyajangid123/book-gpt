# Use a lightweight python image to save memory on Render's free tier
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies needed for compiling PGVector/PostgreSQL drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker's caching mechanism
COPY requirements.txt .

# Install dependencies without saving cache to keep the container lightweight
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your backend runs on (Render automatically detects this)
EXPOSE 8000

# Start your application (assuming you use uvicorn for your API)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
