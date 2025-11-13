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
COPY metadata_regions_config_new.json .

# Create necessary directories
RUN mkdir -p /app/uploads /app/temp /app/logs

# Expose port (Railway will override this with its own PORT)
EXPOSE 8002

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SERVICE_HOST=0.0.0.0

# Run application
# Railway will use the startCommand from railway.toml, but this is the fallback
CMD ["python", "start_server_docker.py"]

