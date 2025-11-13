"""
Startup script for RiftboundOCR Service (Docker/Production)
Production-ready configuration for Railway deployment
"""

import os
import sys
import signal

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("🚀 RiftboundOCR Service Starting...")
print("=" * 60)

# Debug: Check Railway's PORT environment variable
print(f"[DEBUG] Railway PORT env: {os.getenv('PORT')}")
print(f"[DEBUG] SERVICE_PORT env: {os.getenv('SERVICE_PORT')}")

# Import application first to ensure it loads correctly
print("Loading FastAPI application...")
from src.main import app
from src.config import settings

print(f"✓ FastAPI application loaded")
print(f"Service: {settings.app_name} v{settings.app_version}")
print(f"Host: {settings.service_host}")
print(f"Port: {settings.service_port} (configured)")
print(f"GPU: {settings.use_gpu}")
print("=" * 60)

# Import uvicorn for server
import uvicorn

# Graceful shutdown handler
shutdown_requested = False

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    if not shutdown_requested:
        print(f"\n[SHUTDOWN] Received signal {signum}, shutting down gracefully...")
        shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

print("Starting Uvicorn server...")
print("✓ Registered signal handlers for graceful shutdown")
print(f"✓ Ready to accept connections on {settings.service_host}:{settings.service_port}")

# Run server with production settings
try:
    uvicorn.run(
        app,
        host=settings.service_host,
        port=settings.service_port,
        log_level="info",
        access_log=True,
        # Production settings
        timeout_keep_alive=65,  # Keep-alive timeout (Railway uses 60s)
        limit_concurrency=100,  # Max concurrent connections
        backlog=2048  # Connection backlog
    )
except Exception as e:
    print(f"[ERROR] Server failed: {e}")
    sys.exit(1)

