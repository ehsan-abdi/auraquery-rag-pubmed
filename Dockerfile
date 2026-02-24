# Use a lightweight Python 3.11 image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download HuggingFace model into the Docker image cache to avoid IP rate-limiting at runtime
RUN python -c "from langchain_qdrant.fastembed_sparse import FastEmbedSparse; FastEmbedSparse(model_name='Qdrant/bm25')"

# Copy only the necessary backend application code
COPY app/ ./app/

# Cloud Run injects the $PORT environment variable dynamically (usually 8080)
EXPOSE 8080

# Command to run the FastAPI application via Uvicorn
CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
