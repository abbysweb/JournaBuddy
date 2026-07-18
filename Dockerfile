FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy backend requirements first
COPY backend/requirements.txt /app/backend/

# Install torch CPU version first to avoid downloading massive CUDA binaries
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the rest of the application
COPY backend /app/backend
COPY frontend /app/frontend

# Create uploads directory
RUN mkdir -p /app/backend/uploads && chmod 777 /app/backend/uploads

# Set the working directory to backend so that app.py works as expected
WORKDIR /app/backend

# Expose the port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
