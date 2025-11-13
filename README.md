# RiftboundOCR Service

Convert Chinese decklist screenshots to structured deck objects with English card data.

## 🎯 Overview

**Input:** Chinese decklist image (JPG/PNG)  
**Output:** Structured JSON with English card names and metadata  
**Accuracy:** 93-96% card matching, 96% metadata extraction  
**Processing Time:** 30-40 seconds (GCP Production) | 30-60 seconds (local dev)

---

## 🚨 **DEPLOYMENT GUIDES** (Start Here!)

### **⭐ [GCP Cloud Run - PRODUCTION](GCP_PRODUCTION_REFERENCE.md)** 🚀
**Current production deployment** - Live service running on GCP:
- ✅ **30-40 second processing** (20x faster than Railway!)
- ✅ **4 CPUs + 4GB RAM** (dedicated resources)
- ✅ **Auto-scaling** with always-warm instance
- ✅ **$15-25/month** with free tier credit
- ✅ **Production URL**: `https://riftbound-ocr-660047080116.us-central1.run.app`

### **📚 Alternative Deployment Options**
- [GCP Cloud Run Setup Guide](GCP_CLOUD_RUN_DEPLOYMENT.md) - Complete deployment guide with GPU options
- [DigitalOcean Deployment](DIGITALOCEAN_DEPLOYMENT.md) - Self-hosted VPS ($12/month, moderate speed)
- [Railway Deployment](docs/archive/) - Archived (too slow for production)

---

## 📚 **Documentation**

### **Core Documentation**
- **[Complete API Reference](docs/COMPLETE_API_REFERENCE.md)** - All API routes, schemas, examples
- **[Frontend Metadata Guide](docs/FRONTEND_METADATA_GUIDE.md)** - React/Vue integration examples
- **[Streaming Guide](docs/FRONTEND_STREAMING_GUIDE.md)** - Server-Sent Events (SSE) implementation

### **Quick Start Guides**
- [Quick Start](docs/guides/QUICK_START.md) - Get running locally in 5 minutes
- [Local Development](docs/guides/LOCAL_DEVELOPMENT.md) - Development setup
- [Troubleshooting](docs/guides/TROUBLESHOOTING.md) - Common issues

### **Reference**
- [Documentation Index](docs/README.md) - Browse all documentation
- [API Routes Frontend](docs/reference/API_ROUTES_FRONTEND.md) - Frontend-specific API docs

---

## 🚀 Quick Start

### Method 1: Python Script (Recommended)

```bash
# One-time setup and verification
python run_local.py --check

# Start the service
python run_local.py

# Quick test
python test_local.py --quick
```

### Method 2: Shell Scripts

```bash
# Windows
setup_local_dev.bat  # One-time setup
run_dev.bat          # Start service

# Mac/Linux
./setup_local_dev.sh  # One-time setup
./run_dev.sh          # Start service
```

### Test the Service

```bash
# Quick health check
python test_local.py --quick

# Full test with image processing
python test_local.py

# Visit API docs
# http://localhost:8002/docs
```

**Port Configuration:**
- **OCR Service:** 8002 (this service)
- **Main API:** 8000 or 8001  
- **Frontend:** 3000

**See [QUICK_START.md](QUICK_START.md) for detailed instructions.**

## 📁 Project Structure

```
RiftboundOCR/
├── src/
│   ├── ocr/
│   │   ├── parser.py          # Stage 1: Image → Cards
│   │   ├── matcher.py         # Stage 2: Chinese → English
│   │   └── __init__.py
│   ├── api/
│   │   ├── routes.py          # API endpoints
│   │   └── __init__.py
│   ├── models/
│   │   ├── schemas.py         # Pydantic models
│   │   └── __init__.py
│   ├── clients/
│   │   ├── riftbound_api.py   # Main API client
│   │   └── __init__.py
│   ├── utils/
│   │   └── __init__.py
│   └── main.py                # FastAPI app
├── tests/
│   ├── test_parser.py
│   ├── test_matcher.py
│   ├── test_api.py
│   └── test_e2e.py
├── resources/
│   └── card_mappings_final.csv  # 399-card database
├── test_images/               # Sample decklist images
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔌 API Endpoints

### Health Check
```
GET /health
```

### Process Single Image
```
POST /api/v1/process
Content-Type: multipart/form-data

{
  "file": <image file>
}
```

### Process Batch
```
POST /api/v1/process-batch
Content-Type: multipart/form-data

{
  "files": [<image files>]
}
```

### Service Stats
```
GET /api/v1/stats
```

## 🧪 Testing

```bash
# Quick service test
python test_local.py --quick

# Full service test
python test_local.py

# Run test suite
python run_tests.py

# Specific test file
pytest tests/test_parser.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Validate accuracy on test images
python tests/validate_accuracy.py
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t riftbound-ocr:latest .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop service
docker-compose down
```

## 📊 Response Format

```json
{
  "decklist_id": "uuid",
  "metadata": {
    "placement": 92,
    "event": "Season 1 Regionals",
    "date": "2025-09-13"
  },
  "legend": [{
    "name_cn": "无极剑圣",
    "name_en": "Master Yi, The Wuju Bladesman",
    "quantity": 1,
    "card_number": "01IO060",
    "type_en": "Legend",
    "domain_en": "Ionia",
    "match_score": 100
  }],
  "main_deck": [...],
  "battlefields": [...],
  "runes": [...],
  "side_deck": [...],
  "stats": {
    "total_cards": 63,
    "matched_cards": 59,
    "accuracy": 93.65
  }
}
```

## ⚙️ Configuration

Copy `env.example` to `.env` and configure:

```bash
# Service (port 8002 to avoid conflict with main API on 8000/8001)
SERVICE_PORT=8002
DEBUG=false

# Main API Integration
MAIN_API_URL=http://localhost:8000/api  # Local dev
# MAIN_API_URL=https://your-api.vercel.app/api  # Production
MAIN_API_KEY=your-api-key

# OCR Settings
USE_GPU=false
```

## 🔧 Troubleshooting

### Dependencies won't install
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### First run is slow
Models are downloading (~2-3GB). Subsequent runs will be faster.

### Out of memory
OCR models need 2-4GB RAM. Increase Docker memory or use larger instance.

### Low accuracy
- Verify card_mappings_final.csv exists
- Check test images are clear
- Review validation results

## 📚 Documentation

- **[Quick Start](QUICK_START.md)** - Get started in 5 minutes
- **[Deployment Guide](docs/guides/DEPLOYMENT.md)** - Production deployment
- **[API Reference](docs/reference/API_REFERENCE.md)** - Complete API docs
- **[Frontend Integration](docs/reference/FRONTEND_INTEGRATION_CHECKLIST.md)** - Frontend setup
- **[All Documentation](docs/README.md)** - Full documentation index

## 🎯 Performance

### Production (GCP Cloud Run)
- **Processing Time:** 30-40 seconds per image
- **Accuracy:** 93-96% card matching
- **Resources:** 4 vCPUs, 4GB RAM
- **Throughput:** 90-120 images/hour
- **Scaling:** Auto-scales 1-10 instances

### Local Development
- **Processing Time:** 30-60 seconds (varies by CPU)
- **Memory:** 2-4GB RAM
- **GPU Supported:** Yes (10x faster)

## 🤝 Contributing

1. Write tests for new features
2. Ensure all tests pass: `pytest tests/ -v`
3. Follow existing code style
4. Update documentation

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

- PaddleOCR for Chinese text recognition
- EasyOCR for quantity detection
- RapidFuzz for fuzzy matching

---

## 📍 Current Status

**Deployment:** ✅ GCP Cloud Run (Production)  
**Service URL:** `https://riftbound-ocr-660047080116.us-central1.run.app`  
**Performance:** 🚀 30-40 seconds (20x faster than Railway!)  
**Health:** 🟢 Live and Healthy  
**Version:** 1.0.0  
**Last Updated:** November 13, 2025

