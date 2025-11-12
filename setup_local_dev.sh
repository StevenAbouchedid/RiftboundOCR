#!/bin/bash
# Local Development Setup Script for Mac/Linux
# Run this once to set up your dev environment

echo "============================================"
echo "RiftboundOCR - Local Development Setup"
echo "============================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python not found! Please install Python 3.10+"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo "[3/5] Upgrading pip..."
pip install --upgrade pip

echo "[4/5] Installing dependencies (this will take 10-15 minutes)..."
echo "This will download ~2-3GB of ML models on first run"
pip install -r requirements.txt

echo "[5/5] Creating .env file..."
if [ ! -f .env ]; then
    cp env.example .env
    echo "Created .env file - please edit it with your settings"
else
    echo ".env already exists - skipping"
fi

echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your local settings"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python src/main.py"
echo "4. Visit: http://localhost:8002/docs"
echo ""
echo "Note: OCR service runs on port 8002"
echo "      Main API runs on port 8000 or 8001"
echo ""
echo "For testing:"
echo "   python tests/validate_accuracy.py"
echo ""

