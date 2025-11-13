# Railway Healthcheck Debugging Guide

## 🎯 Current Status

### ✅ Build: SUCCESS (31 seconds!)
```
[92mBuild time: 31.07 seconds[0m
```

### ❌ Healthcheck: FAILING
```
[93mAttempt #1-6 failed with service unavailable[0m
[91mHealthcheck failed![0m
```

---

## 🔍 What We've Fixed

### Fix #1: CPU-only PyTorch ✅
- **Result:** Build time reduced from 15+ min to 31 sec
- **Status:** Working perfectly

### Fix #2: Copy startup script ✅
- **Added:** `COPY start_server_docker.py .`
- **Status:** File is being copied

### Fix #3: Railway PORT variable ✅
- **Problem:** Railway uses `PORT` env var, we were using `SERVICE_PORT`
- **Fix:** Updated `src/config.py` to check both
- **Code:**
```python
service_port: int = int(os.getenv("PORT") or os.getenv("SERVICE_PORT") or "8002")
```

### Fix #4: Simplified startup script ✅
- **Created:** `start_server_docker.py` (no Windows-specific code)
- **Removed:** DLL loading code that might cause issues on Linux
- **Added:** More debug output to see what's happening

---

## 🚨 Possible Issues

### Issue #1: Service Takes Too Long to Start

**Problem:** OCR models take 30-60 seconds to load

**Evidence:**
- Healthcheck attempts: 10s, 21s, 33s, 48s, 66s, 92s
- Service never responds even after 90+ seconds

**Solutions to try:**

**A. Check Railway Application Logs**

In Railway dashboard:
1. Click on your deployment
2. Go to "Logs" tab
3. Look for application output like:
   ```
   🚀 RiftboundOCR Service Starting...
   Loading FastAPI application...
   Starting Uvicorn server...
   ```

**If you see errors**, that's the problem!

**Common errors:**
- `ModuleNotFoundError` - Missing dependency
- `FileNotFoundError` - Missing file
- Model download errors - First run needs to download models

---

### Issue #2: Port Binding Problem

**Problem:** Service might be binding to wrong port

**Check in Railway logs for:**
```
Uvicorn running on http://0.0.0.0:XXXX
```

**Expected:** Port should match Railway's `$PORT` (usually random)

**Fix:** Already applied in `src/config.py`

---

### Issue #3: Models Need to Download

**Problem:** First deployment downloads 2-3GB of OCR models

**Timeline:**
- PaddleOCR models: ~1GB, 30-60 sec download
- EasyOCR models: ~2GB, 60-120 sec download
- **Total first start: 2-3 minutes**

**Solution:** Increase healthcheck timeout

**Already updated in `railway.toml`:**
```toml
healthcheckTimeout = 120  # Increased from 100
```

**But Railway might not respect this!**

---

## 🛠️ Debug Steps

### Step 1: Check Application Logs

**In Railway Dashboard → Logs**, look for:

**✅ Good (service starting):**
```
🚀 RiftboundOCR Service Starting...
Loading FastAPI application...
Service: RiftboundOCR Service v1.0.0
Host: 0.0.0.0
Port: XXXX
Starting Uvicorn server...
INFO:     Started server process [XX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

**❌ Bad (service crashing):**
```
ModuleNotFoundError: No module named 'xxx'
FileNotFoundError: [Errno 2] No such file or directory: 'xxx'
Error loading models...
```

---

### Step 2: Check Port Binding

**In logs, find:**
```
Uvicorn running on http://0.0.0.0:XXXX
```

**The XXXX should match Railway's PORT**

To verify, add this to `start_server_docker.py`:
```python
print(f"Railway PORT env: {os.getenv('PORT')}")
print(f"Using port: {settings.service_port}")
```

---

### Step 3: Manual Health Check

**Once service is running, test manually:**

```bash
# Get your Railway URL
RAILWAY_URL="https://your-app.up.railway.app"

# Test health endpoint
curl -v $RAILWAY_URL/api/v1/health

# Should return:
# HTTP/1.1 200 OK
# {"status":"healthy","service":"RiftboundOCR",...}
```

---

### Step 4: Test Locally with Docker

**Build and run locally to verify it works:**

```bash
# Build
docker build -t test-ocr .

# Run (Railway sets PORT automatically, we'll set it manually)
docker run -p 8002:8002 -e PORT=8002 test-ocr

# In another terminal
curl http://localhost:8002/api/v1/health
```

**Expected output:**
```
🚀 RiftboundOCR Service Starting...
Loading FastAPI application...
...
INFO:     Application startup complete.
```

---

## 📊 Files Changed in This Fix

| File | Change | Purpose |
|------|--------|---------|
| `Dockerfile` | Use `start_server_docker.py` | Simpler startup |
| `railway.toml` | Use `start_server_docker.py` + timeout 120s | Match Docker CMD |
| `src/config.py` | Read `PORT` or `SERVICE_PORT` | Railway compatibility |
| `start_server_docker.py` | NEW - Simplified startup | No Windows code |

---

## 🚀 Next Steps

### 1. Push These Changes

```bash
git add Dockerfile railway.toml src/config.py start_server_docker.py RAILWAY_HEALTHCHECK_DEBUG.md
git commit -m "Fix Railway healthcheck: simplified startup + PORT support"
git push origin main
```

### 2. Check Railway Logs

**Immediately after deployment:**
1. Go to Railway Dashboard
2. Click on your deployment
3. View "Logs" tab
4. **Look for application startup messages**

### 3. Report Back

**Tell me what you see in the logs:**

**A. If you see startup messages:**
```
🚀 RiftboundOCR Service Starting...
Loading FastAPI application...
```
→ Service is starting, might just need more time

**B. If you see errors:**
```
ModuleNotFoundError: ...
FileNotFoundError: ...
```
→ Copy the error and I'll help fix it

**C. If you see nothing (empty logs):**
→ Container might not be starting at all

---

## 🔧 Alternative: Use Uvicorn Directly

**If the custom startup script causes issues, simplify even more:**

**Update `railway.toml`:**
```toml
[deploy]
startCommand = "python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT"
```

**Update `Dockerfile` CMD:**
```dockerfile
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

This bypasses any startup script issues.

---

## 📞 What to Check

**Please check Railway logs and tell me:**

1. ✅ Do you see `🚀 RiftboundOCR Service Starting...`?
2. ✅ Do you see `INFO: Uvicorn running on...`?
3. ✅ What port does it say it's running on?
4. ❌ Do you see any errors?
5. ❌ Are the logs completely empty?

**This will tell us exactly what's wrong!** 🔍

