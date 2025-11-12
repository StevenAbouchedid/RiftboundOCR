#!/usr/bin/env python3
"""
RiftboundOCR Local Development Runner

A comprehensive script to run the OCR service locally for development and testing.

Usage:
    python run_local.py              # Run with default settings
    python run_local.py --check      # Only verify setup, don't start server
    python run_local.py --test       # Run tests after starting server
    python run_local.py --port 8003  # Use custom port
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Terminal colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.ENDC}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")

def check_python_version():
    """Check if Python version is 3.10+"""
    print_info("Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error(f"Python 3.10+ required, found {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_venv():
    """Check if virtual environment is activated"""
    print_info("Checking virtual environment...")
    
    # Check if we're in a venv
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if not in_venv:
        print_warning("Virtual environment not detected")
        print_info("Consider activating venv:")
        if os.name == 'nt':  # Windows
            print(f"  {Colors.BOLD}venv\\Scripts\\activate{Colors.ENDC}")
        else:  # Unix
            print(f"  {Colors.BOLD}source venv/bin/activate{Colors.ENDC}")
        return False
    
    print_success("Virtual environment active")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print_info("Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'paddleocr',
        'easyocr',
        'PIL',
        'cv2',
        'rapidfuzz',
        'pydantic',
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'PIL':
                __import__('PIL')
            elif package == 'cv2':
                __import__('cv2')
            else:
                __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print_error(f"Missing packages: {', '.join(missing)}")
        print_info("Install with: pip install -r requirements.txt")
        return False
    
    print_success("All dependencies installed")
    return True

def check_env_file():
    """Check if .env file exists"""
    print_info("Checking environment configuration...")
    
    if not os.path.exists('.env'):
        print_warning(".env file not found")
        
        if os.path.exists('env.example'):
            print_info("Creating .env from env.example...")
            try:
                with open('env.example', 'r', encoding='utf-8') as src:
                    content = src.read()
                with open('.env', 'w', encoding='utf-8') as dst:
                    dst.write(content)
                print_success("Created .env file")
                print_warning("Please review and update .env with your settings")
                return True
            except Exception as e:
                print_error(f"Failed to create .env: {e}")
                return False
        else:
            print_error("env.example not found")
            return False
    
    print_success(".env file exists")
    return True

def check_card_mappings():
    """Check if card mappings file exists"""
    print_info("Checking card mappings...")
    
    mapping_paths = [
        'resources/card_mappings_final.csv',
        'src/ocr/data/card_mappings_final.csv',
    ]
    
    for path in mapping_paths:
        if os.path.exists(path):
            # Get file size
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print_success(f"Card mappings found: {path} ({size_mb:.2f} MB)")
            
            # Count lines (cards)
            try:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    line_count = sum(1 for _ in f) - 1  # Subtract header
                print_info(f"  Contains {line_count} card mappings")
            except Exception:
                pass
            
            return True
    
    print_error("Card mappings file not found")
    print_info("Expected location: resources/card_mappings_final.csv")
    return False

def check_test_images():
    """Check if test images exist"""
    print_info("Checking test images...")
    
    if not os.path.exists('test_images'):
        print_warning("test_images directory not found")
        return False
    
    # Count image files
    image_extensions = ['.jpg', '.jpeg', '.png']
    images = [
        f for f in os.listdir('test_images')
        if os.path.splitext(f)[1].lower() in image_extensions
    ]
    
    if not images:
        print_warning("No test images found in test_images/")
        return False
    
    print_success(f"Found {len(images)} test image(s)")
    return True

def check_port_available(port):
    """Check if port is available"""
    import socket
    
    print_info(f"Checking if port {port} is available...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            print_success(f"Port {port} is available")
            return True
        except OSError:
            print_error(f"Port {port} is already in use")
            print_info("Change port with: python run_local.py --port 8003")
            return False

def load_env_config():
    """Load configuration from .env file"""
    config = {
        'SERVICE_PORT': 8002,
        'SERVICE_HOST': '0.0.0.0',
        'DEBUG': 'true',
        'MAIN_API_URL': 'http://localhost:8000/api',
    }
    
    if os.path.exists('.env'):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        except Exception as e:
            print_warning(f"Failed to parse .env: {e}")
    
    return config

def print_config_info(config):
    """Print current configuration"""
    print(f"\n{Colors.BOLD}Current Configuration:{Colors.ENDC}")
    print(f"  Host:           {config.get('SERVICE_HOST', '0.0.0.0')}")
    print(f"  Port:           {config.get('SERVICE_PORT', 8002)}")
    print(f"  Debug:          {config.get('DEBUG', 'true')}")
    print(f"  Main API:       {config.get('MAIN_API_URL', 'Not set')}")
    print(f"  GPU:            {config.get('USE_GPU', 'false')}")

def run_setup_checks():
    """Run all setup checks"""
    print_header("RiftboundOCR Setup Verification")
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_venv),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Card Mappings", check_card_mappings),
        ("Test Images", check_test_images),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    # Summary
    print(f"\n{Colors.BOLD}Setup Summary:{Colors.ENDC}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{Colors.GREEN}✓{Colors.ENDC}" if result else f"{Colors.RED}✗{Colors.ENDC}"
        print(f"  {status} {name}")
    
    print(f"\n{Colors.BOLD}Result: {passed}/{total} checks passed{Colors.ENDC}")
    
    return all(results.values())

def start_server(port=None, host='0.0.0.0', reload=True):
    """Start the FastAPI development server"""
    print_header("Starting Development Server")
    
    config = load_env_config()
    
    if port is None:
        port = int(config.get('SERVICE_PORT', 8002))
    
    print_config_info(config)
    
    # Check if port is available
    if not check_port_available(port):
        print_error("Cannot start server - port in use")
        return False
    
    print(f"\n{Colors.BOLD}Server URLs:{Colors.ENDC}")
    print(f"  API Docs:       {Colors.CYAN}http://localhost:{port}/docs{Colors.ENDC}")
    print(f"  ReDoc:          {Colors.CYAN}http://localhost:{port}/redoc{Colors.ENDC}")
    print(f"  Health Check:   {Colors.CYAN}http://localhost:{port}/api/v1/health{Colors.ENDC}")
    print(f"  API Root:       {Colors.CYAN}http://localhost:{port}/api/v1{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Press CTRL+C to stop the server{Colors.ENDC}\n")
    
    time.sleep(1)
    
    # Start uvicorn
    try:
        import uvicorn
        
        # Add project root to Python path for proper module resolution
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        uvicorn.run(
            "src.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        return True
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Server stopped by user{Colors.ENDC}")
        return True
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        return False

def run_tests():
    """Run the test suite"""
    print_header("Running Test Suite")
    
    print_info("Starting pytest...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
            check=False
        )
        
        if result.returncode == 0:
            print_success("All tests passed!")
            return True
        else:
            print_error("Some tests failed")
            return False
    except Exception as e:
        print_error(f"Failed to run tests: {e}")
        return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='RiftboundOCR Local Development Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_local.py              # Run server with default settings
  python run_local.py --check      # Only verify setup
  python run_local.py --port 8003  # Use custom port
  python run_local.py --test       # Run tests
  python run_local.py --no-reload  # Disable auto-reload
        """
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Only run setup checks, do not start server'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run tests instead of starting server'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Port to run server on (default: 8002 from .env)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--no-reload',
        action='store_true',
        help='Disable auto-reload on code changes'
    )
    
    args = parser.parse_args()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run setup checks
    if not run_setup_checks():
        print_error("\nSetup checks failed!")
        print_info("Fix the issues above and try again")
        
        if not args.check:
            response = input(f"\n{Colors.YELLOW}Continue anyway? (y/N): {Colors.ENDC}")
            if response.lower() != 'y':
                sys.exit(1)
    else:
        print_success("\nAll setup checks passed!")
    
    # If --check only, exit
    if args.check:
        print_info("\nCheck complete. Use 'python run_local.py' to start server")
        sys.exit(0)
    
    # If --test, run tests
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # Start the server
    print_info("\nStarting server in 2 seconds...")
    time.sleep(2)
    
    success = start_server(
        port=args.port,
        host=args.host,
        reload=not args.no_reload
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

