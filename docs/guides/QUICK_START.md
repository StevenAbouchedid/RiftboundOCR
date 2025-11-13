# Quick Start Guide

Fast setup and testing for local development.

---

## 🚀 Initial Setup (First Time Only)

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
setup_local_dev.bat
```

**Mac/Linux:**
```bash
chmod +x setup_local_dev.sh
./setup_local_dev.sh
```

### Option 2: Python Script

```bash
python run_local.py --check
```

This will:
- ✅ Check Python version
- ✅ Verify virtual environment
- ✅ Check dependencies
- ✅ Create .env file
- ✅ Verify card mappings
- ✅ Check test images

---

## 🏃 Run the Service

### Quick Start

```bash
# Windows
run_dev.bat

# Mac/Linux
./run_dev.sh

# Or use Python script (cross-platform)
python run_local.py
```

### Advanced Options

```bash
# Only verify setup (don't start server)
python run_local.py --check

# Use custom port
python run_local.py --port 8003

# Disable auto-reload
python run_local.py --no-reload

# Run tests instead of server
python run_local.py --test
```

---

## 🧪 Test the Service

### Quick Health Check

```bash
python test_local.py --quick
```

### Full Test (with image processing)

```bash
python test_local.py
```

### Test Specific Image

```bash
python test_local.py --image test_images/Screenshot_20251106_021827_WeChat.jpg
```

### Test Remote Server

```bash
python test_local.py --url https://your-service.railway.app
```

---

## 🔍 Manual Testing

### 1. Health Check

```bash
curl http://localhost:8002/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "RiftboundOCR Service",
  "version": "1.0.0",
  "matcher_loaded": true,
  "total_cards_in_db": 399
}
```

### 2. Service Stats

```bash
curl http://localhost:8002/api/v1/stats
```

### 3. Process Image

```bash
curl -X POST http://localhost:8002/api/v1/process \
  -F "file=@test_images/Screenshot_20251106_021827_WeChat.jpg"
```

### 4. API Documentation

Visit in browser:
- **Swagger UI:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc

---

## 📊 Run Test Suite

### All Tests

```bash
python run_tests.py
```

### Specific Test File

```bash
pytest tests/test_matcher.py -v
```

### With Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Validate Accuracy

```bash
python tests/validate_accuracy.py
```

---

## 🔧 Common Commands

### Start Development

```bash
# Activate venv (if not already)
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Start server
python run_local.py
```

### Quick Test

```bash
python test_local.py --quick
```

### Full Test

```bash
python test_local.py
```

### Run Test Suite

```bash
python run_tests.py
```

### Verify Setup

```bash
python run_local.py --check
```

---

## 🌐 Service URLs

| Endpoint | URL |
|----------|-----|
| **API Docs** | http://localhost:8002/docs |
| **ReDoc** | http://localhost:8002/redoc |
| **Health** | http://localhost:8002/api/v1/health |
| **Stats** | http://localhost:8002/api/v1/stats |
| **Process** | http://localhost:8002/api/v1/process |
| **Batch** | http://localhost:8002/api/v1/process-batch |

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Use different port
python run_local.py --port 8003
```

### Venv Not Activated

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Missing Dependencies

```bash
pip install -r requirements.txt
```

### Card Mappings Not Found

Make sure `resources/card_mappings_final.csv` exists.

### Service Won't Start

```bash
# Verify setup
python run_local.py --check

# Check logs for errors
```

---

## 📋 Development Workflow

### Daily Workflow

1. **Start of day:**
   ```bash
   cd RiftboundOCR
   python run_local.py
   ```

2. **Make code changes** (auto-reloads in debug mode)

3. **Test changes:**
   ```bash
   python test_local.py --quick
   ```

4. **Before commit:**
   ```bash
   python run_tests.py
   ```

### Testing New Features

1. **Write tests first** (TDD approach):
   ```bash
   # Add test to tests/test_*.py
   ```

2. **Run specific test:**
   ```bash
   pytest tests/test_matcher.py::test_specific_function -v
   ```

3. **Implement feature**

4. **Verify all tests pass:**
   ```bash
   python run_tests.py
   ```

5. **Test manually:**
   ```bash
   python test_local.py
   ```

---

## 🚀 Ready for Production?

### Pre-Deploy Checklist

```bash
# 1. Run all tests
python run_tests.py

# 2. Validate accuracy
python tests/validate_accuracy.py

# 3. Test health endpoint
python test_local.py --quick

# 4. Test full processing
python test_local.py
```

### Deploy to Railway

See **DEPLOYMENT.md** for detailed instructions.

---

## 📚 More Information

- **Full Setup:** `SETUP_INSTRUCTIONS.md`
- **Local Development:** `LOCAL_DEVELOPMENT.md`
- **Deployment:** `DEPLOYMENT.md`
- **API Reference:** `docs/API.md`
- **Architecture:** `docs/ARCHITECTURE.md`

---

## 💡 Tips

### Speed Up Development

1. **Keep server running** - Auto-reloads on code changes (when DEBUG=true)
2. **Use --quick flag** - Fast health checks without full processing
3. **Test specific files** - `pytest tests/test_file.py` instead of full suite
4. **Use Python scripts** - Cross-platform and feature-rich

### Improve Accuracy

1. **Update card mappings** - Add new cards to `resources/card_mappings_final.csv`
2. **Test with real images** - Use actual decklist screenshots
3. **Review validation results** - `python tests/validate_accuracy.py`
4. **Check unmatched cards** - Look for patterns in failures

### Debug Issues

1. **Enable detailed logging** - Set `DEBUG=true` in `.env`
2. **Check health endpoint** - Verify service is running
3. **Review logs** - Check console output for errors
4. **Test components individually** - Use Python REPL to test parser/matcher

---

**Happy Coding!** 🎉





