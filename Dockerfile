# Use a lightweight Python 3.12 image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for compiling psycopg2 and some HF logic)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 1. Install core Python packages first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Fix for Exit Code 1: Pre-install specific HuggingFace dependencies 
# This ensures the download script has everything it needs to run
RUN pip install --no-cache-dir sentence-transformers langchain-huggingface

# 3. PRE-DOWNLOAD MODEL WEIGHTS
# We set HUGGINGFACE_HUB_CACHE to a standard path to ensure persistent caching
ENV HUGGINGFACE_HUB_CACHE=/root/.cache/huggingface
RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')"

# 4. Copy your application code
COPY . .

# Expose port and start app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
