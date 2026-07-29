FROM python:3.10-slim

WORKDIR /app

# System dependencies for PyMuPDF and general utilities
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first to keep image size small
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ./app ./app

# Copy Alembic migration configuration and scripts
COPY alembic.ini .
COPY ./alembic ./alembic

# Expose FastAPI port
EXPOSE 8000
