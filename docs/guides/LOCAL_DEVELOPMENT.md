# Local Development Guide

Quick guide for running RiftboundOCR locally for development.

---

## 🚀 Quick Start

### **Windows**

```bash
# One-time setup
setup_local_dev.bat

# Daily development
run_dev.bat
```

### **Mac/Linux**

```bash
# One-time setup
chmod +x setup_local_dev.sh run_dev.sh
./setup_local_dev.sh

# Daily development
./run_dev.sh
```

---

## 📍 Port Configuration

| Service | Port | URL |
|---------|------|-----|
| **Main API** | 8000 or 8001 | http://localhost:8000 |
| **OCR Service** | 8002 | http://localhost:8002 |
| **Frontend** | 3000 | http://localhost:3000 |

---

## 🔧 Manual Setup

If you prefer to set up manually:

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**First install takes 10-15 minutes** (downloads ~2-3GB of ML models)

### 3. Configure Environment

```bash
# Copy template
copy env.example .env  # Windows
# cp env.example .env  # Mac/Linux

# Edit with your settings
notepad .env  # Windows
# nano .env    # Mac/Linux
```

**Local .env example:**
```bash
# Service runs on port 8002 (Main API uses 8000/8001)
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8002
DEBUG=true

# Point to your local main API
MAIN_API_URL=http://localhost:8000/api

# Or if your main API is on 8001
# MAIN_API_URL=http://localhost:8001/api

USE_GPU=false
ENABLE_LOGGING=true
ALLOWED_ORIGINS=*
```

### 4. Run the Service

```bash
python src/main.py
```

**Output:**
```
🚀 RiftboundOCR Service v1.0.0
================================================================
Debug mode: True
Main API: http://localhost:8000/api
================================================================
INFO:     Uvicorn running on http://0.0.0.0:8002
```

**Visit:** http://localhost:8002/docs

---

## 🧪 Testing Locally

### Health Check

```bash
curl http://localhost:8002/api/v1/health
```

### Process Test Image

```bash
curl -X POST http://localhost:8002/api/v1/process \
  -F "file=@test_images/Screenshot_20251106_021827_WeChat.jpg"
```

### Run Test Suite

```bash
# Activate venv first
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Run all tests
python run_tests.py

# Run validation on test images
python tests/validate_accuracy.py
```

---

## 🔄 Full Local Stack

Run all services together:

### Terminal 1: OCR Service (Port 8002)

```bash
cd RiftboundOCR
venv\Scripts\activate
python src/main.py
```

### Terminal 2: Main API (Port 8000 or 8001)

```bash
cd RiftboundTopDecks-API
# Follow your main API local dev process
python run_local.py
```

### Terminal 3: Frontend (Port 3000)

```bash
cd frontend
npm run dev
```

### Configure Integration

**Main API .env:**
```bash
# Add OCR service URL
OCR_SERVICE_URL=http://localhost:8002
```

**OCR Service .env:**
```bash
# Point to main API
MAIN_API_URL=http://localhost:8000/api
# or
MAIN_API_URL=http://localhost:8001/api
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :8002  # Windows
# lsof -i :8002  # Mac/Linux

# Change port in .env if needed
SERVICE_PORT=8003
```

### Models Not Downloading

```bash
# Manually trigger model download
python -c "from paddleocr import PaddleOCR; PaddleOCR()"
python -c "import easyocr; easyocr.Reader(['en'])"
```

### Import Errors

```bash
# Ensure venv is activated
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### Can't Connect to Main API

Check your .env:
```bash
# Make sure URL matches your main API
MAIN_API_URL=http://localhost:8000/api

# Or try with trailing slash
MAIN_API_URL=http://localhost:8000/api/
```

---

## 💡 Development Tips

### Hot Reload

When DEBUG=true, the server auto-reloads on code changes:

```bash
# Edit src/ocr/parser.py
# Server automatically restarts
```

### View Logs

Logs output directly to console when DEBUG=true:

```
INFO:     127.0.0.1:52341 - "POST /api/v1/process HTTP/1.1" 200 OK
INFO:     Processing image: test.jpg
INFO:     ✓ Parsed 42 cards
INFO:     ✓ Matched 40/42 cards (95.2%)
```

### Test Individual Components

```python
# Test parser only
from src.ocr.parser import parse_decklist
result = parse_decklist('test_images/Screenshot_20251106_021827_WeChat.jpg')
print(result)

# Test matcher only
from src.ocr.matcher import match_cards
matched = match_cards(result)
print(f"Accuracy: {matched['stats']['accuracy']}%")
```

---

## 📚 Quick Reference

### Start Development

```bash
# Windows
run_dev.bat

# Mac/Linux
./run_dev.sh
```

### URLs

- **API Docs:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc
- **Health:** http://localhost:8002/api/v1/health
- **Stats:** http://localhost:8002/api/v1/stats

### Common Commands

```bash
# Activate environment
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# Run server
python src/main.py

# Run tests
python run_tests.py

# Validate accuracy
python tests/validate_accuracy.py

# Verify setup
python verify_setup.py
```

---

## ✅ Daily Workflow

1. **Start of day:**
   ```bash
   cd RiftboundOCR
   run_dev.bat  # or ./run_dev.sh
   ```

2. **Make changes** to code

3. **Test changes** (auto-reloads in debug mode)

4. **Run tests** before committing:
   ```bash
   python run_tests.py
   ```

5. **Commit and push** (Railway auto-deploys on push)

---

## 🚀 Ready to Deploy?

When you're ready to deploy to production:

See **DEPLOYMENT.md** for Railway deployment instructions.





