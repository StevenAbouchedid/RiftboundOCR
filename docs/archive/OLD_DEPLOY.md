# 🚀 Quick Deploy Guide

## Railway (Recommended - 5 minutes)

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Deploy
railway up

# 5. Get your URL
railway domain
```

**Cost:** ~$5-10/month

---

## Docker (Self-Hosted)

```bash
# 1. Configure environment
cp env.example .env
# Edit .env with your settings

# 2. Start service
docker-compose up -d

# 3. Check health
curl http://localhost:8002/api/v1/health
```

---

## Render

```bash
# 1. Connect your GitHub repo at render.com
# 2. Select "Docker" environment
# 3. Set health check: /api/v1/health
# 4. Deploy
```

**Cost:** $7/month (Starter plan)

---

## Environment Variables

Required in `.env`:

```bash
SERVICE_PORT=8002
DEBUG=false
USE_GPU=false
MAIN_API_URL=https://your-api.com/api
```

---

## After Deployment

1. **Test health:**
   ```bash
   curl https://your-service.railway.app/api/v1/health
   ```

2. **Test processing:**
   ```bash
   curl -X POST https://your-service.railway.app/api/v1/process \
     -F "file=@test_image.jpg"
   ```

3. **Update frontend:**
   ```bash
   # Add to your frontend .env
   OCR_SERVICE_URL=https://your-service.railway.app
   ```

---

## Full Documentation

See [docs/guides/DEPLOYMENT.md](docs/guides/DEPLOYMENT.md) for complete deployment guide.

