FROM python:3.11-slim

# Install system dependencies for audio/video processing
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render/Cloud Run injects the PORT env variable)
ENV PORT=8000
EXPOSE $PORT

# Start FastAPI server
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
