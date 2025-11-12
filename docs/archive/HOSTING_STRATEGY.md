# RiftboundOCR Hosting Strategy

**Aligned with RiftboundTopDecks-API practices**

---

## 🚨 Important: OCR Service Architecture Constraints

The OCR service has **unique requirements** that prevent standard Vercel serverless deployment:

| Requirement | Value | Vercel Limit | Status |
|------------|-------|--------------|--------|
| Model Size | 2-3 GB | 250 MB | ❌ Too large |
| Memory | 2-4 GB | 1 GB max | ❌ Insufficient |
| Processing Time | 30-60s | 60s timeout | ⚠️ At limit |
| Cold Start | ~30s | N/A | ❌ Too slow |

**Conclusion:** Core OCR processing **cannot** run on Vercel serverless.

---

## ✅ Recommended: Hybrid Architecture

Follow your standard practices where possible, use dedicated hosting for OCR processing:

```
┌─────────────────────────────────────────┐
│         VERCEL (Standard)               │
│  ┌──────────────────────────────────┐   │
│  │   OCR API Gateway (Lightweight)  │   │  ← YOUR STANDARD STACK
│  │   - Request validation           │   │  ← Vercel Serverless
│  │   - Job queue                    │   │  ← Branch deployments
│  │   - Status tracking              │   │  ← Environment vars
│  └──────────────┬───────────────────┘   │
└─────────────────┼───────────────────────┘
                  │ HTTP
                  ↓
┌─────────────────────────────────────────┐
│    DEDICATED SERVER (Exception)         │
│  ┌──────────────────────────────────┐   │
│  │   OCR Processing Worker          │   │  ← Docker on VPS/Railway
│  │   - PaddleOCR + EasyOCR          │   │  ← 2-3GB models
│  │   - Image processing             │   │  ← Heavy computation
│  │   - Card matching                │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 📦 Option 1: Vercel API Gateway + Railway Worker (Recommended)

### Architecture

**Vercel Service (Follows your standards):**
- ✅ Lightweight API gateway
- ✅ Branch-based deployments (main, develop, feature/*)
- ✅ Environment variables in dashboard
- ✅ Standard FastAPI structure
- ✅ No Docker needed

**Railway/Render Worker (OCR processing):**
- Heavy OCR processing only
- Deployed via Docker (unavoidable for models)
- Single production instance

### Setup

#### Part A: Vercel API Gateway (Your Standard Stack)

```bash
riftbound-ocr-api/
├── api/
│   └── index.py              # Vercel entry point
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app
│   ├── config.py             # Settings (Vercel standard)
│   └── routers/
│       └── ocr.py            # OCR endpoints
├── requirements.txt          # Lightweight deps only
├── vercel.json              # Vercel config
├── run_local.py             # Local dev
├── .env.example
└── README.md
```

**requirements.txt (Lightweight - Vercel compatible):**
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
httpx==0.26.0              # For calling OCR worker
python-dotenv==1.0.0
```

**app/config.py (Following your pattern):**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    """Settings following RiftboundTopDecks-API patterns"""
    
    # Service info
    app_name: str = "RiftboundOCR API Gateway"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Main API connection
    main_api_url: str = "https://riftbound-api.vercel.app/api"
    main_api_key: str = ""
    
    # OCR Worker connection
    ocr_worker_url: str = "https://your-ocr-worker.railway.app"
    ocr_worker_key: str = ""
    
    # CORS (your standard)
    allowed_origins: str = "*"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_allowed_origins_list(self) -> List[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]

settings = Settings()
```

**vercel.json (Standard):**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

**Environment Variables (Vercel Dashboard):**

| Environment | Variable | Value |
|-------------|----------|-------|
| **Development** | `OCR_WORKER_URL` | `http://localhost:8000` |
| **Development** | `MAIN_API_URL` | `http://localhost:8000/api` |
| **Preview** | `OCR_WORKER_URL` | `https://ocr-worker-staging.railway.app` |
| **Preview** | `MAIN_API_URL` | `https://riftbound-api-git-dev.vercel.app/api` |
| **Production** | `OCR_WORKER_URL` | `https://ocr-worker.railway.app` |
| **Production** | `MAIN_API_URL` | `https://riftbound-api.vercel.app/api` |

#### Part B: Railway Worker (OCR Processing)

Deploy existing Docker setup to Railway.app:

```bash
# Deploy to Railway
railway login
railway init
railway up

# Set environment variables
railway variables set USE_GPU=false
railway variables set ENABLE_LOGGING=true

# Railway auto-assigns URL
# Example: https://riftbound-ocr-production.railway.app
```

**Cost:** Railway free tier includes 500 hours/month (~$5/month after)

---

## 📦 Option 2: Vercel-Only (Simplified, Limited)

If you want to stay 100% on Vercel, we need to **drastically simplify**:

### What This Means

- ❌ Remove PaddleOCR (300MB models)
- ❌ Remove EasyOCR (1GB models)
- ✅ Use lightweight OCR API (e.g., Google Cloud Vision API)
- ✅ Only card matching logic on Vercel
- ⚠️ Lower accuracy, external API costs

### Simplified Architecture

```python
# External OCR API instead of local models
import httpx

async def extract_text(image_bytes: bytes) -> str:
    """Use Google Cloud Vision instead of local OCR"""
    # Call external OCR API
    response = await httpx.post(
        "https://vision.googleapis.com/v1/images:annotate",
        json={...}
    )
    return response.json()
```

**Not recommended** - Loses accuracy and adds external dependencies.

---

## 📦 Option 3: Vercel Functions + Background Jobs

Use Vercel for API, offload processing to background queue:

### Architecture

```
Frontend → Vercel API → Redis Queue → Railway Worker
                ↓
         Job Status Polling
```

### Implementation

**Vercel API (app/routers/ocr.py):**
```python
from fastapi import APIRouter, UploadFile
import httpx
import uuid

router = APIRouter()

@router.post("/process")
async def queue_ocr_job(file: UploadFile):
    """Queue OCR job (non-blocking)"""
    job_id = str(uuid.uuid4())
    
    # Upload to temporary storage (S3/R2)
    image_url = await upload_to_storage(file)
    
    # Queue job to worker
    await queue_job(job_id, image_url)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/status/{job_id}"
    }

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Poll job status"""
    status = await get_job_status_from_redis(job_id)
    return status
```

**Worker processes asynchronously** on Railway/Render.

---

## 🎯 Recommended Setup: Option 1 (Hybrid)

### Your Standard Practices (Vercel)

✅ **Follows all your patterns:**
- Branch-based deployments (main → prod, develop → preview)
- Environment variables in Vercel dashboard
- No Docker on Vercel side
- Standard FastAPI structure
- `run_local.py` for development
- `.env` for local, Vercel dashboard for deployed

### Exception for OCR Worker

❌ **Must break standard for worker:**
- Docker required (no way around ML models)
- Deploy to Railway/Render (can't use Vercel)
- Single production instance
- Manual deployment (not git-based)

---

## 🛠️ Implementation Plan

### Phase 1: Create Vercel API Gateway

Following your exact patterns:

```bash
# Create new service
mkdir riftbound-ocr-api
cd riftbound-ocr-api

# Standard structure
mkdir -p api app/routers
touch api/index.py
touch app/{__init__.py,main.py,config.py}
touch app/routers/{__init__.py,ocr.py}
touch requirements.txt vercel.json run_local.py .env.example

# Follow NEW_SERVICE_HOSTING_GUIDE.md exactly
```

### Phase 2: Deploy Worker to Railway

```bash
# Use existing Docker setup
cd ../RiftboundOCR
railway login
railway init
railway up

# Get worker URL
railway domain
# Example: https://riftbound-ocr.railway.app
```

### Phase 3: Configure Vercel

```bash
# Standard Vercel workflow
cd ../riftbound-ocr-api
vercel login
vercel

# Add environment variables in dashboard
# Settings → Environment Variables
# - OCR_WORKER_URL (dev/preview/prod)
# - MAIN_API_URL (dev/preview/prod)
```

### Phase 4: Connect Frontend

Frontend → Vercel API Gateway → Railway Worker

No changes to frontend integration needed!

---

## 📊 Environment Matrix

| Environment | API Gateway | OCR Worker | Main API |
|-------------|-------------|------------|----------|
| **Local Dev** | localhost:8001 | localhost:8000 | localhost:8000 |
| **Preview** | ocr-api-git-*.vercel.app | ocr-staging.railway.app | api-git-dev.vercel.app |
| **Production** | ocr-api.vercel.app | ocr-prod.railway.app | api.vercel.app |

---

## 💰 Cost Analysis

### Option 1: Hybrid (Recommended)

| Service | Cost | Notes |
|---------|------|-------|
| Vercel API | Free | Under limits |
| Railway Worker | $5-10/month | Dedicated resources |
| **Total** | **$5-10/month** | Best performance |

### Option 2: All Vercel (Not viable)

Cannot work due to model size.

### Option 3: Queue-Based

| Service | Cost | Notes |
|---------|------|-------|
| Vercel API | Free | Under limits |
| Railway Worker | $5-10/month | Processing only |
| Redis | $0-5/month | Upstash free tier |
| S3/R2 Storage | $0-1/month | Minimal |
| **Total** | **$5-16/month** | More complexity |

---

## 🎯 Recommended Action

### What I'll Build

1. **Lightweight Vercel API Gateway** (100% your standards)
   - Follows NEW_SERVICE_HOSTING_GUIDE.md exactly
   - Branch deployments
   - Environment variables in dashboard
   - No Docker

2. **Keep existing OCR worker** (unavoidable exception)
   - Deploy to Railway (one command)
   - Docker for ML models
   - Single production instance

3. **Update documentation**
   - Clarify why worker needs different hosting
   - Provide Railway deployment guide
   - Maintain your standard practices everywhere else

### What You Get

- ✅ 95% follows your practices
- ✅ Only OCR processing is exception
- ✅ Frontend integration unchanged
- ✅ Branch-based deployments (where possible)
- ✅ Vercel dashboard for config
- ✅ $5-10/month total cost

---

## 🚀 Next Steps

Should I:

**Option A:** Create the Vercel API Gateway following your standards, deploy worker to Railway?

**Option B:** Keep it simple - just deploy existing service to Railway with better docs?

**Option C:** Simplify to external OCR API (lower quality but 100% Vercel)?

**Which approach do you prefer?** 🤔





