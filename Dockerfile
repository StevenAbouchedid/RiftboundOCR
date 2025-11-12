# Dockerfile for RiftboundOCR Service
# Production-ready container with OCR models

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and OCR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
# IMPORTANT: Install CPU-only PyTorch FIRST to avoid massive CUDA dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    torch==2.9.1+cpu \
    torchvision==0.24.1+cpu \
    --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY resources/ ./resources/
COPY start_server_docker.py .

# Create necessary directories
RUN mkdir -p /app/uploads /app/temp /app/logs

# Expose port
EXPOSE 8002

# Health check (Railway uses its own healthcheck path, but this is a backup)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/api/v1/health', timeout=5)"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SERVICE_HOST=0.0.0.0 \
    SERVICE_PORT=8002

# Run application
# Railway will use the startCommand from railway.toml, but this is the fallback
CMD ["python", "start_server_docker.py"]

