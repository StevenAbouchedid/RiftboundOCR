# RiftboundOCR Documentation

Complete documentation for the RiftboundOCR service - Chinese decklist OCR and card matching API.

---

## 📚 Quick Navigation

### **Getting Started**
- [Quick Start Guide](../QUICK_START.md) - Get up and running in 5 minutes
- [Setup Instructions](../SETUP_INSTRUCTIONS.md) - Detailed installation guide
- [Local Development](../LOCAL_DEVELOPMENT.md) - Development workflow

### **API Documentation**
- **[Complete API Reference](COMPLETE_API_REFERENCE.md)** ⭐ **START HERE** - Full technical documentation
  - All routes with examples
  - Request/response schemas
  - Hosting & deployment guide
  - Environment configuration
  - Performance & scaling
- [Frontend Integration Guide](FRONTEND_METADATA_GUIDE.md) - How to use the API from frontend
- [Frontend Metadata Summary](../FRONTEND_METADATA_SUMMARY.md) - Quick metadata integration guide
- [API Routes Reference](reference/API_ROUTES_FRONTEND.md) - Frontend-focused API guide

### **Features**
- [Position-Based Metadata Extraction](POSITION_BASED_METADATA_EXTRACTION.md) - Advanced metadata extraction
- [Streaming Guide](STREAMING_GUIDE.md) - SSE streaming for batch uploads

### **Deployment**
- [Deployment Guide](../DEPLOYMENT.md) - Production deployment overview
- [Docker Guide](../Dockerfile) - Container deployment
- [Railway Configuration](../railway.toml) - Railway.app deployment

### **Project Information**
- [Project Status](../PROJECT_STATUS.md) - Current status and roadmap
- [Final Summary](../FINAL_SUMMARY.md) - Project completion summary
- [Troubleshooting](../TROUBLESHOOTING.md) - Common issues and solutions

### **Reference**
- [Bug Report for Upstream](../BUG_REPORT_FOR_UPSTREAM.md) - Known issues in source repo

---

## 📋 Documentation Structure

```
RiftboundOCR/
├── docs/
│   ├── README.md (this file)
│   ├── COMPLETE_API_REFERENCE.md          ⭐ Main API docs
│   ├── FRONTEND_METADATA_GUIDE.md         Frontend integration
│   ├── POSITION_BASED_METADATA_EXTRACTION.md  Advanced features
│   ├── STREAMING_GUIDE.md                 SSE streaming
│   └── reference/
│       └── API_ROUTES_FRONTEND.md         Quick API reference
│
├── QUICK_START.md                         Get started quickly
├── SETUP_INSTRUCTIONS.md                  Installation guide
├── DEPLOYMENT.md                          Deploy to production
├── PROJECT_STATUS.md                      Project overview
└── TROUBLESHOOTING.md                     Problem solving
```

---

## 🎯 Documentation by Use Case

### **I want to integrate the API into my frontend**
1. Read: [Frontend Metadata Summary](../FRONTEND_METADATA_SUMMARY.md) (Quick overview)
2. Read: [Frontend Metadata Guide](FRONTEND_METADATA_GUIDE.md) (Complete guide with code examples)
3. Reference: [Complete API Reference](COMPLETE_API_REFERENCE.md) (Full technical details)

### **I want to deploy the service**
1. Read: [Complete API Reference - Hosting Section](COMPLETE_API_REFERENCE.md#hosting--deployment)
2. Read: [Deployment Guide](../DEPLOYMENT.md)
3. Configure: Use [railway.toml](../railway.toml) or [docker-compose.yml](../docker-compose.yml)

### **I want to understand the metadata extraction**
1. Read: [Frontend Metadata Summary](../FRONTEND_METADATA_SUMMARY.md) (What changed)
2. Read: [Position-Based Metadata Extraction](POSITION_BASED_METADATA_EXTRACTION.md) (How it works)

### **I want to set up locally for development**
1. Read: [Quick Start](../QUICK_START.md)
2. Read: [Local Development](../LOCAL_DEVELOPMENT.md)
3. Reference: [Setup Instructions](../SETUP_INSTRUCTIONS.md)

### **I want to understand streaming batch uploads**
1. Read: [Streaming Guide](STREAMING_GUIDE.md)
2. See examples in: [Complete API Reference - Streaming Endpoint](COMPLETE_API_REFERENCE.md#5-process-batch-streaming---sse)

---

## 🔑 Key Features

### **Metadata Extraction (96% Accuracy)**
- ✅ Player names
- ✅ Deck names
- ✅ Tournament placement
- ✅ Event names
- ✅ Dates

**See:** [Frontend Metadata Guide](FRONTEND_METADATA_GUIDE.md)

### **Card Matching (93-96% Accuracy)**
- ✅ 322 cards in database
- ✅ 5 matching strategies
- ✅ Fuzzy matching
- ✅ Confidence scores

**See:** [Complete API Reference](COMPLETE_API_REFERENCE.md)

### **Multiple Processing Modes**
- ✅ Single image processing (30-60s)
- ✅ Batch processing (sequential)
- ✅ Streaming batch (SSE with progress)
- ✅ Parallel batch (50-70% faster)

**See:** [Streaming Guide](STREAMING_GUIDE.md)

---

## 🚀 Quick Links

| Resource | Link |
|----------|------|
| **Main API Docs** | [COMPLETE_API_REFERENCE.md](COMPLETE_API_REFERENCE.md) |
| **Swagger UI** | `http://localhost:8002/docs` |
| **ReDoc** | `http://localhost:8002/redoc` |
| **Health Check** | `http://localhost:8002/api/v1/health` |
| **GitHub** | *[Your GitHub URL]* |

---

## 📊 API Endpoints Summary

| Endpoint | Method | Purpose | Processing Time |
|----------|--------|---------|-----------------|
| `/api/v1/health` | GET | Health check | <1s |
| `/api/v1/stats` | GET | Service statistics | <1s |
| `/api/v1/process` | POST | Single image | 30-60s |
| `/api/v1/process-batch` | POST | Batch (sequential) | 30-60s × N |
| `/api/v1/process-batch-stream` | POST | Batch (streaming) | 30-60s × N |
| `/api/v1/process-batch-fast` | POST | Batch (parallel) | 15-30s × N |

**Full details:** [Complete API Reference](COMPLETE_API_REFERENCE.md#api-routes-reference)

---

## 🎨 Response Structure

```typescript
{
  decklist_id: "uuid",
  metadata: {
    player: "Ai.闪闪",              // NEW!
    deck_name: "卡莎",              // NEW!
    placement: 1,                   // IMPROVED!
    event: "...",                   // IMPROVED!
    date: "2025-08-30",            // IMPROVED!
    legend_name_en: "Kai'Sa, ..."  // NEW!
  },
  legend: [...],
  main_deck: [...],
  battlefields: [...],
  runes: [...],
  side_deck: [...],
  unmatched: [...],
  stats: {
    total_cards: 63,
    matched_cards: 59,
    accuracy: 93.65
  }
}
```

**Full schema:** [Complete API Reference - Schemas](COMPLETE_API_REFERENCE.md#requestresponse-schemas)

---

## 🔧 Configuration

### **Environment Variables**

Key settings:
```bash
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8002
USE_GPU=false
MAX_FILE_SIZE_MB=10
CARD_MAPPING_PATH=resources/card_mappings_final.csv
```

**Full list:** [Complete API Reference - Configuration](COMPLETE_API_REFERENCE.md#environment-configuration)

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| **Processing Time** | 30-60s per image |
| **Accuracy** | 93-96% (cards), 96% (metadata) |
| **Throughput** | 60-120 images/hour |
| **Memory Usage** | 1.5-2GB |

**Optimization guide:** [Complete API Reference - Performance](COMPLETE_API_REFERENCE.md#performance--scaling)

---

## 🐛 Troubleshooting

**Common Issues:**
- Service unavailable → Check `/health` endpoint
- Slow processing → Check image resolution (1080p optimal)
- Low accuracy → Verify image quality and language
- OOM errors → Increase memory or disable GPU

**Full guide:** [Troubleshooting](../TROUBLESHOOTING.md)

---

## 📞 Support

- **Issues:** GitHub Issues
- **API Docs:** `/docs` (Swagger UI)
- **Email:** *[Your email]*

---

## 🔄 Recent Updates

### November 2025 - Version 1.0.0
- ✅ Position-based metadata extraction (96% accuracy)
- ✅ Player name & deck name extraction
- ✅ SSE streaming for batch processing
- ✅ Complete API documentation

**Changelog:** [Complete API Reference - Changelog](COMPLETE_API_REFERENCE.md#changelog)

---

## 📝 Contributing

See [GitHub repository] for contribution guidelines.

---

## License

See LICENSE file in repository.

---

## Summary

This documentation covers:
- ✅ **Complete API reference** with all endpoints
- ✅ **Frontend integration guides** with code examples
- ✅ **Deployment guides** for Railway, Docker, VPS
- ✅ **Configuration** and environment setup
- ✅ **Performance** optimization and scaling
- ✅ **Troubleshooting** common issues

**Start with:** [Complete API Reference](COMPLETE_API_REFERENCE.md) 🚀
