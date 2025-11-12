"""
Startup script for RiftboundOCR Service (Docker/Production)
Simplified version without Windows-specific code
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("🚀 RiftboundOCR Service Starting...")
print("=" * 60)

# Import and run
print("Loading FastAPI application...")
from src.main import app
from src.config import settings

print(f"Service: {settings.app_name} v{settings.app_version}")
print(f"Host: {settings.service_host}")
print(f"Port: {settings.service_port}")
print(f"GPU: {settings.use_gpu}")
print("=" * 60)

# Start server
import uvicorn

print("Starting Uvicorn server...")
uvicorn.run(
    app,
    host=settings.service_host,
    port=settings.service_port,
    log_level="info",
    access_log=True
)

