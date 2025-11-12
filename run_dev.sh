#!/bin/bash
# Quick development server starter for Mac/Linux

echo "Starting RiftboundOCR Development Server..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run setup_local_dev.sh first"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found!"
    echo "Creating from template..."
    cp env.example .env
    echo "Please edit .env with your settings"
    read -p "Press enter to continue..."
fi

# Start server
echo ""
echo "============================================"
echo "Starting OCR service on http://localhost:8002"
echo "API Docs: http://localhost:8002/docs"
echo "Main API should be on port 8000 or 8001"
echo "Press CTRL+C to stop"
echo "============================================"
echo ""

python src/main.py

