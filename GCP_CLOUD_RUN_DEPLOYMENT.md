# Google Cloud Run Deployment Guide

## Why Cloud Run for OCR?

- ✅ **Faster CPU** than Railway (dedicated cores)
- ✅ **Auto-scaling** (only pay when processing)
- ✅ **GPU option** available (10x faster for OCR!)
- ✅ **No cold starts** with minimum instances
- ✅ **Cost-effective** for OCR workloads

**Expected Performance:**
- CPU only: 30-60 seconds
- With GPU: **5-15 seconds** 🚀

---

## Prerequisites

1. **Google Cloud Account** (free tier includes $300 credit)
2. **gcloud CLI** installed (or use Cloud Shell)
3. **Docker** installed locally (optional - Cloud Build can do this)

---

## Step 1: Set Up GCP Project

### 1.1 Create a New Project

```bash
# Install gcloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Login to GCP
gcloud auth login

# Create a new project
gcloud projects create riftbound-ocr --name="Riftbound OCR"

# Set as active project
gcloud config set project riftbound-ocr

# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com
```

### 1.2 Set Up Billing

Go to: https://console.cloud.google.com/billing
- Link your project to a billing account
- You get **$300 free credit** for 90 days!

---

## Step 2: Prepare Your Application

### 2.1 Create Cloud Run Configuration

Create `cloudrun.yaml`:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: riftbound-ocr
  labels:
    cloud.googleapis.com/location: us-central1
spec:
  template:
    metadata:
      annotations:
        # Scale up quickly for OCR requests
        autoscaling.knative.dev/minScale: '1'  # Keep 1 instance warm (no cold starts)
        autoscaling.knative.dev/maxScale: '10'  # Scale up to 10 instances
        # CPU and memory allocation
        run.googleapis.com/cpu-throttling: 'false'  # Always allocated
        run.googleapis.com/execution-environment: gen2  # Better performance
    spec:
      containerConcurrency: 2  # Max 2 concurrent requests per instance
      timeoutSeconds: 300  # 5-minute timeout for long OCR requests
      containers:
      - image: gcr.io/riftbound-ocr/ocr-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: '8080'
        - name: USE_GPU
          value: 'false'  # Set to 'true' when GPU is configured
        - name: PYTHONUNBUFFERED
          value: '1'
        - name: TQDM_DISABLE
          value: '1'
        resources:
          limits:
            # Start with CPU, upgrade to GPU later
            cpu: '4'      # 4 vCPUs (can adjust: 1, 2, 4, 8)
            memory: 4Gi   # 4GB RAM (can adjust: 2Gi, 4Gi, 8Gi, 16Gi)
```

### 2.2 Update Dockerfile for Cloud Run

Your existing `Dockerfile` should work, but let's optimize it:

Create `.dockerignore` if you don't have one:

```
# .dockerignore
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.git/
.gitignore
.vscode/
.idea/
*.md
!README.md
test_images/
docs/
.env
*.log
temp/
uploads/
logs/
```

Your `Dockerfile` looks good as-is! Cloud Run will use it.

---

## Step 3: Build and Deploy

### Option A: Using Cloud Build (Recommended - No Docker needed locally)

```bash
# Build the container using Cloud Build
gcloud builds submit --tag gcr.io/riftbound-ocr/ocr-service:latest

# Deploy to Cloud Run
gcloud run deploy riftbound-ocr \
  --image gcr.io/riftbound-ocr/ocr-service:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --cpu 4 \
  --memory 4Gi \
  --timeout 300 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 2 \
  --set-env-vars "USE_GPU=false,PYTHONUNBUFFERED=1,TQDM_DISABLE=1"
```

### Option B: Using Docker Locally

```bash
# Build locally
docker build -t gcr.io/riftbound-ocr/ocr-service:latest .

# Push to Google Container Registry
docker push gcr.io/riftbound-ocr/ocr-service:latest

# Deploy
gcloud run deploy riftbound-ocr \
  --image gcr.io/riftbound-ocr/ocr-service:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --cpu 4 \
  --memory 4Gi \
  --timeout 300 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 2
```

---

## Step 4: Configure Your Service

### 4.1 Set Environment Variables

```bash
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --set-env-vars "USE_GPU=false,PYTHONUNBUFFERED=1,TQDM_DISABLE=1"
```

### 4.2 Get Your Service URL

```bash
gcloud run services describe riftbound-ocr \
  --region us-central1 \
  --format 'value(status.url)'
```

This will output something like:
```
https://riftbound-ocr-xxxxx-uc.a.run.app
```

Update your frontend to use this URL!

---

## Step 5: (Optional) Add GPU Support 🚀

**Note**: GPU support requires:
1. Special quota request (contact GCP support)
2. Higher costs (~$0.40/hour when running)
3. But **10x faster OCR** (5-15 seconds instead of 60+)

### 5.1 Request GPU Quota

1. Go to: https://console.cloud.google.com/iam-admin/quotas
2. Search for "Cloud Run GPUs"
3. Request increase to 1+ GPUs for your region

### 5.2 Deploy with GPU

```bash
gcloud beta run deploy riftbound-ocr \
  --image gcr.io/riftbound-ocr/ocr-service:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --memory 8Gi \
  --timeout 300 \
  --min-instances 1 \
  --max-instances 5 \
  --set-env-vars "USE_GPU=true,PYTHONUNBUFFERED=1,TQDM_DISABLE=1"
```

**GPU Options:**
- `nvidia-l4`: Best value ($0.40/hr) - Recommended
- `nvidia-t4`: Cheaper ($0.35/hr) but older
- `nvidia-a100`: Most powerful ($2.50/hr) - overkill for OCR

---

## Step 6: Cost Optimization

### Current Setup Cost Estimate

**Without GPU (CPU only):**
- Instance time: $0.00002400/vCPU-second
- Memory: $0.00000250/GiB-second
- Requests: Free (first 2M/month)

**Example calculation** (moderate usage):
- 1000 requests/month
- 60 seconds avg per request
- 4 vCPUs, 4GB RAM
- **Cost: ~$15-20/month**

**With 1 GPU:**
- GPU time: $0.40/hour when running
- Only pay when processing
- Example: 1000 requests × 10 seconds = ~3 hours
- **GPU cost: ~$1.20/month** (for processing only!)
- Total: **~$20-25/month**

### Cost Optimization Tips

#### 1. Keep 1 Instance Warm (Prevent Cold Starts)

```bash
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --min-instances 1  # Costs ~$10/month but ensures instant response
```

Or use 0 to save money but accept 10-30 second cold starts:

```bash
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --min-instances 0  # Save $10/month, accept cold starts
```

#### 2. Reduce CPU/Memory When Not Needed

```bash
# For lower traffic, reduce resources
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --cpu 2 \
  --memory 2Gi
```

#### 3. Set Request Timeout

```bash
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --timeout 300  # 5 minutes max
```

---

## Step 7: Monitoring and Logs

### View Logs

```bash
# Stream logs
gcloud run services logs tail riftbound-ocr --region us-central1

# Or view in console
# https://console.cloud.google.com/run
```

### Set Up Monitoring

```bash
# Enable monitoring
gcloud services enable monitoring.googleapis.com

# Create uptime check
gcloud monitoring uptime create riftbound-ocr-health \
  --resource-type uptime-url \
  --url "https://your-service-url.run.app/health" \
  --period 300
```

---

## Step 8: CI/CD (Automatic Deployments)

### Option A: Cloud Build Trigger (GitHub)

1. Go to: https://console.cloud.google.com/cloud-build/triggers
2. Click "Connect Repository" → Link your GitHub repo
3. Create trigger:
   - Branch: `main`
   - Build config: `cloudbuild.yaml`

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/ocr-service:$COMMIT_SHA', '.']
  
  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/ocr-service:$COMMIT_SHA']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'riftbound-ocr'
      - '--image=gcr.io/$PROJECT_ID/ocr-service:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'

images:
  - 'gcr.io/$PROJECT_ID/ocr-service:$COMMIT_SHA'
```

### Option B: GitHub Actions

Create `.github/workflows/deploy-gcp.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: riftbound-ocr
    
    - name: Configure Docker
      run: gcloud auth configure-docker
    
    - name: Build and Push
      run: |
        docker build -t gcr.io/riftbound-ocr/ocr-service:$GITHUB_SHA .
        docker push gcr.io/riftbound-ocr/ocr-service:$GITHUB_SHA
    
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy riftbound-ocr \
          --image gcr.io/riftbound-ocr/ocr-service:$GITHUB_SHA \
          --region us-central1 \
          --platform managed
```

---

## Comparison: Cloud Run vs Railway

| Feature | Railway | Cloud Run (CPU) | Cloud Run (GPU) |
|---------|---------|-----------------|-----------------|
| **OCR Speed** | 5+ minutes ❌ | 30-60 seconds ✅ | **5-15 seconds** 🚀 |
| **Cost** | $10-20/month | $15-25/month | $20-30/month |
| **CPU** | Shared | 4 dedicated vCPUs | 2-8 vCPUs + GPU |
| **Memory** | 1-2GB | 4GB | 8GB |
| **Cold Starts** | No | Yes (10-30s) | Yes (30-60s) |
| **Auto-scaling** | No | Yes | Yes |
| **Setup** | Easy | Medium | Medium |

---

## Quick Start Commands

```bash
# 1. Set up project
gcloud config set project riftbound-ocr
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# 2. Build and deploy (one command!)
gcloud run deploy riftbound-ocr \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --cpu 4 \
  --memory 4Gi \
  --timeout 300 \
  --min-instances 1

# 3. Get URL
gcloud run services describe riftbound-ocr \
  --region us-central1 \
  --format 'value(status.url)'
```

That's it! Your OCR service will be live and **much faster** than Railway! 🚀

---

## Troubleshooting

### Build Fails
```bash
# Check build logs
gcloud builds list
gcloud builds log [BUILD_ID]
```

### Service Won't Start
```bash
# Check service logs
gcloud run services logs read riftbound-ocr --region us-central1
```

### Out of Memory
```bash
# Increase memory
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --memory 8Gi
```

### Too Slow?
1. Increase CPU: `--cpu 8`
2. Increase memory: `--memory 8Gi`
3. Or add GPU (see Step 5)

---

## Next Steps

1. Deploy to Cloud Run using the commands above
2. Test with your frontend
3. Monitor costs in GCP Console
4. If still slow, request GPU quota and deploy with GPU

Good luck! 🚀

