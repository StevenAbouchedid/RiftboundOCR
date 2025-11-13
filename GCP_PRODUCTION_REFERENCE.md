# GCP Cloud Run Production Reference

> **Production Deployment Guide** - Quick reference for the live GCP Cloud Run service

---

## 🚀 Production Service Information

### Service Details
- **Service Name**: `riftbound-ocr`
- **Service URL**: `https://riftbound-ocr-660047080116.us-central1.run.app`
- **Region**: `us-central1`
- **Project ID**: `riftbound-ocr`

### Performance
- **Processing Time**: 30-40 seconds per image (with 4 CPUs)
- **Accuracy**: 93-96% card matching
- **Uptime**: Min 1 instance (no cold starts)
- **Max Scale**: 10 instances

---

## 📍 API Endpoints

### Production Base URL
```
https://riftbound-ocr-660047080116.us-central1.run.app
```

### Available Endpoints

#### Health Check
```
GET /health
GET /api/v1/health

Response: {
  "status": "healthy",
  "service": "RiftboundOCR Service",
  "version": "1.0.0",
  "matcher_loaded": true,
  "total_cards_in_db": 322
}
```

#### Process Image (Streaming)
```
POST /api/v1/process-stream
Content-Type: multipart/form-data

Body:
  file: <image file>

Response: Server-Sent Events (SSE)
  - progress events
  - result event (final decklist)
  - complete event
```

#### Process Image (Standard)
```
POST /api/v1/process
Content-Type: multipart/form-data

Body:
  file: <image file>

Response: JSON decklist
```

---

## 🔧 Configuration

### Current Resource Allocation
- **CPU**: 4 vCPUs (dedicated, no throttling)
- **Memory**: 4 GB RAM
- **Timeout**: 300 seconds (5 minutes)
- **Concurrency**: 2 requests per instance
- **Min Instances**: 1 (always warm)
- **Max Instances**: 10 (auto-scales)

### Environment Variables
```bash
USE_GPU=false
TQDM_DISABLE=1
PORT=8080  # Set automatically by Cloud Run
```

---

## 🖥️ Management Commands

### View Service Status
```bash
gcloud run services describe riftbound-ocr \
  --region us-central1 \
  --format='table(status.conditions.type,status.conditions.status)'
```

### View Logs
```bash
# Recent logs
gcloud run services logs read riftbound-ocr \
  --region us-central1 \
  --limit 100

# Follow logs in real-time
gcloud run services logs tail riftbound-ocr \
  --region us-central1

# Filter errors only
gcloud run services logs read riftbound-ocr \
  --region us-central1 \
  --filter="severity>=ERROR"
```

### View Metrics
```bash
# Get service URL
gcloud run services describe riftbound-ocr \
  --region us-central1 \
  --format='value(status.url)'

# Get traffic info
gcloud run services describe riftbound-ocr \
  --region us-central1 \
  --format='table(status.traffic)'
```

---

## 🔄 Deployment

### Deploy New Version
```bash
# From Cloud Shell or local machine with gcloud CLI

# Navigate to repo
cd ~/RiftboundOCR  # or your local path

# Pull latest changes
git pull origin main

# Deploy
gcloud run deploy riftbound-ocr \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 4 \
  --memory 4Gi \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1 \
  --set-env-vars "USE_GPU=false,TQDM_DISABLE=1"
```

### Rollback to Previous Version
```bash
# List revisions
gcloud run revisions list \
  --service riftbound-ocr \
  --region us-central1

# Rollback to specific revision
gcloud run services update-traffic riftbound-ocr \
  --region us-central1 \
  --to-revisions REVISION_NAME=100
```

---

## 🧪 Testing

### Test Health Endpoint
```bash
curl https://riftbound-ocr-660047080116.us-central1.run.app/health
```

### Test OCR Processing
```bash
curl -X POST \
  -F "file=@test_images/Screenshot_20251106_021827_WeChat.jpg" \
  https://riftbound-ocr-660047080116.us-central1.run.app/api/v1/process
```

### Test Streaming Endpoint
```bash
curl -X POST \
  -F "file=@test_images/Screenshot_20251106_021827_WeChat.jpg" \
  -H "Accept: text/event-stream" \
  https://riftbound-ocr-660047080116.us-central1.run.app/api/v1/process-stream
```

---

## 📊 Monitoring

### Access Cloud Console
- **Service Dashboard**: https://console.cloud.google.com/run/detail/us-central1/riftbound-ocr?project=riftbound-ocr
- **Logs**: https://console.cloud.google.com/run/detail/us-central1/riftbound-ocr/logs?project=riftbound-ocr
- **Metrics**: https://console.cloud.google.com/run/detail/us-central1/riftbound-ocr/metrics?project=riftbound-ocr

### Key Metrics to Watch
- **Request Count**: Should stay consistent
- **Request Latency**: 30-40s for OCR, <1s for health
- **Instance Count**: Should be 1 (min) when idle
- **Error Rate**: Should be <1%
- **Memory Usage**: Should stay under 4GB

---

## 🐛 Troubleshooting

### Service Not Responding
```bash
# Check service status
gcloud run services describe riftbound-ocr --region us-central1

# Check recent logs
gcloud run services logs read riftbound-ocr --region us-central1 --limit 50

# Restart by deploying
gcloud run services update riftbound-ocr --region us-central1
```

### Slow Performance
```bash
# Check if instances are scaling
gcloud run services describe riftbound-ocr \
  --region us-central1 \
  --format='value(spec.template.spec.containerConcurrency)'

# Increase CPU if needed
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --cpu 8  # Upgrade to 8 CPUs
```

### Memory Issues
```bash
# Check memory usage in logs
gcloud run services logs read riftbound-ocr \
  --region us-central1 \
  --filter="textPayload:memory"

# Increase memory if needed
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --memory 8Gi  # Upgrade to 8GB
```

### Cold Starts
```bash
# Verify min instances is set
gcloud run services describe riftbound-ocr \
  --region us-central1 \
  --format='value(spec.template.metadata.annotations[run.googleapis.com/minScale])'

# Should show: 1
```

---

## 💰 Cost Management

### Current Costs (Estimated)
- **Always-on instance (1 min)**: ~$10-15/month
- **Processing time (4 CPU)**: ~$0.000024 per second
- **Memory (4GB)**: ~$0.0000025 per GB-second
- **Requests**: Free (first 2 million)
- **Network egress**: ~$0.12 per GB

### Typical Monthly Cost
- **With 1 min instance + moderate usage**: $15-25/month
- **vs Railway**: $10-20/month (but 10x slower)
- **vs DigitalOcean**: $12/month (2x slower)

### Cost Optimization
```bash
# Reduce min instances to 0 (adds cold starts)
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --min-instances 0

# Reduce CPU to 2 (slower processing)
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --cpu 2

# Reduce memory to 2GB
gcloud run services update riftbound-ocr \
  --region us-central1 \
  --memory 2Gi
```

---

## 🔐 Security

### Authentication
Currently **unauthenticated** (public access). To add authentication:

```bash
# Remove public access
gcloud run services remove-iam-policy-binding riftbound-ocr \
  --region us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"

# Add specific users
gcloud run services add-iam-policy-binding riftbound-ocr \
  --region us-central1 \
  --member="user:your-email@example.com" \
  --role="roles/run.invoker"
```

### CORS
Already configured in backend to accept:
- `https://riftboundtopdecks.com`
- `http://localhost:3000` (dev)

To add more origins, update `src/main.py`:
```python
origins = [
    "https://riftboundtopdecks.com",
    "https://your-new-domain.com",  # Add here
]
```

---

## 🚀 Future Upgrades

### Add GPU Support (10x Faster!)
```bash
# Deploy with GPU (requires special region)
gcloud run deploy riftbound-ocr \
  --source . \
  --region us-central1 \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --cpu 4 \
  --memory 16Gi \
  --set-env-vars "USE_GPU=true"

# Expected: 5-15 seconds processing time
```

### Increase Resources
```bash
# Max out CPU and memory
gcloud run deploy riftbound-ocr \
  --source . \
  --region us-central1 \
  --cpu 8 \
  --memory 16Gi
```

### Add Custom Domain
```bash
# Map custom domain
gcloud run domain-mappings create \
  --service riftbound-ocr \
  --domain ocr.yourdomain.com \
  --region us-central1
```

---

## 📞 Support

- **GCP Console**: https://console.cloud.google.com/run?project=riftbound-ocr
- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **Support**: https://cloud.google.com/support

---

## 📝 Change Log

### 2025-11-13: Initial Deployment
- Deployed to GCP Cloud Run with 4 CPUs, 4GB RAM
- Set min instances to 1 (no cold starts)
- Processing time: 30-40 seconds (20x faster than Railway)
- Status: ✅ Production Ready

---

**Service Status**: 🟢 Live and Healthy  
**Last Updated**: November 13, 2025  
**Next Review**: Monitor costs after 1 week

