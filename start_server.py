"""
Startup script for RiftboundOCR Service
Handles Windows DLL loading issues before starting the server
"""

import os
import sys

# Configure console encoding for Windows FIRST
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Windows DLL loading fix - MUST happen before any torch imports
print("Setting up PyTorch DLL paths for Windows...")
try:
    # First, import torch to trigger its own initialization
    import torch
    
    # Add torch lib directory to PATH and DLL search path
    torch_lib_path = os.path.join(os.path.dirname(torch.__file__), 'lib')
    if os.path.exists(torch_lib_path):
        # Add to PATH
        if torch_lib_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
        
        # Add to DLL search directories (Python 3.8+)
        try:
            os.add_dll_directory(torch_lib_path)
            print(f"[OK] Added torch DLL directory: {torch_lib_path}")
        except Exception as e:
            print(f"Warning: Could not add DLL directory: {e}")
    
    print(f"[OK] PyTorch {torch.__version__} loaded successfully")
    
except Exception as e:
    print(f"[ERROR] Error loading PyTorch: {e}")
    print("The server may not start correctly.")
    sys.exit(1)

# Now that torch is loaded, we can import the rest of the application
print("Starting FastAPI application...")

from src.main import app
import uvicorn
from src.config import settings

# Configure console encoding for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

if __name__ == "__main__":
    print("=" * 60)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("=" * 60)
    print(f"Host: {settings.service_host}:{settings.service_port}")
    print(f"Debug: {settings.debug}")
    print(f"GPU: {settings.use_gpu}")
    print("=" * 60)
    
    # DON'T use reload on Windows - causes issues with PyTorch DLLs
    uvicorn.run(
        app,
        host=settings.service_host,
        port=settings.service_port,
        reload=False,  # Never use reload on Windows with PyTorch
        log_level="info" if settings.enable_logging else "warning"
    )

