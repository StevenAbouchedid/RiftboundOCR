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

# Debug: Environment and system info
print(f"[DEBUG] Python: {sys.version}")
print(f"[DEBUG] CWD: {os.getcwd()}")
print(f"[DEBUG] Railway PORT env: {os.getenv('PORT')}")
print(f"[DEBUG] SERVICE_PORT env: {os.getenv('SERVICE_PORT')}")
print(f"[DEBUG] Files in /app: {os.listdir('/app') if os.path.exists('/app') else 'N/A'}")
print(f"[DEBUG] Resources exists: {os.path.exists('resources')}")
if os.path.exists('resources'):
    print(f"[DEBUG] Resources contents: {os.listdir('resources')}")

# Import application first to ensure it loads correctly
print("\n[STARTUP] Loading FastAPI application...")
try:
    from src.main import app
    from src.config import settings
    print("✓ FastAPI application loaded successfully")
except Exception as e:
    print(f"❌ CRITICAL: Failed to load application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"✓ Service: {settings.app_name} v{settings.app_version}")
print(f"✓ Host: {settings.service_host}")
print(f"✓ Port: {settings.service_port} (configured)")
print(f"✓ GPU: {settings.use_gpu}")
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

print("\n[STARTUP] Starting Uvicorn server...")
print("✓ Registered signal handlers for graceful shutdown")
print(f"✓ Ready to accept connections on {settings.service_host}:{settings.service_port}")
print(f"✓ Health check endpoints: /health and /api/v1/health")
print("=" * 60)

# Run server with production settings
try:
    print("[SERVER] Uvicorn starting...")
    uvicorn.run(
        app,
        host=settings.service_host,
        port=settings.service_port,
        log_level="info",
        access_log=True,
        # Production settings
        timeout_keep_alive=65,  # Keep-alive timeout (Railway uses 60s)
        limit_concurrency=100,  # Max concurrent connections
        backlog=2048,  # Connection backlog
        # Logging
        log_config=None  # Use default logging config
    )
    print("[SERVER] Uvicorn stopped normally")
except KeyboardInterrupt:
    print("\n[SERVER] Received keyboard interrupt, shutting down...")
except Exception as e:
    print(f"\n[ERROR] Server failed with exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

