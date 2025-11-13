# Railway 502 "Connection Refused" Error - Debugging Guide

## Current Situation

Railway deployment shows:
- ✅ Container starts successfully
- ✅ Uvicorn reports listening on port 8080
- ✅ ONE internal health check succeeds (from Railway's internal IP)
- ❌ All subsequent requests fail with **502 "connection refused"**

## Error Pattern

```
upstreamErrors: "connection refused" (retried 3 times)
```

This specific error means Railway's edge proxy **cannot establish a TCP connection** to the container port.

## Possible Root Causes

### 1. **Service Crashes After First Request** ⚠️ MOST LIKELY
- **Symptom**: First health check works, then all fail
- **Cause**: OCR model initialization or resource loading fails on first real request
- **Evidence**: Service responds once, then stops

**What we did to fix:**
- Added comprehensive error logging throughout startup
- Made health checks return 200 even when matcher fails (avoid restart loops)
- Added try-catch blocks around all initialization code
- Added file system debugging to verify resources exist

### 2. **Missing Resources in Container** ⚠️ LIKELY
- **Symptom**: Service starts but matcher fails to load
- **Cause**: `resources/card_mappings_final.csv` not copied to container
- **Evidence**: Would show in logs as matcher initialization failure

**What we did to fix:**
- Added debug logging to check if resources directory exists
- Added logging to show file paths being accessed
- Dockerfile already copies resources/ directory, but we verify now

### 3. **Railway Health Check Configuration Issue**
- **Symptom**: Service gets restarted due to failed health checks
- **Cause**: Health check path mismatch or too aggressive retry
- **Current Config**: 
  - Path: `/api/v1/health`
  - Initial delay: 30s
  - Period: 30s
  - Timeout: 10s per check
  - Failure threshold: 3

**What we did to fix:**
- Changed health checks to return 200 (not 503) even when degraded
- Added `/health` endpoint at root level (frontend uses this)
- Added keep-alive headers to health check responses
- Prevents Railway from restarting container unnecessarily

### 4. **Uvicorn Timeout/Connection Issues**
- **Symptom**: Uvicorn stops accepting connections
- **Cause**: Misconfigured timeouts or connection limits

**What we did to fix:**
- Set `timeout_keep_alive=65` (Railway uses 60s)
- Set `limit_concurrency=100` 
- Set `backlog=2048`
- Added graceful shutdown handlers (SIGTERM/SIGINT)

### 5. **Port Binding Issues**
- **Symptom**: Service binds to wrong port or interface
- **Cause**: Environment variable misconfiguration

**Current behavior:**
- Railway sets `PORT=8080`
- Our config reads: `PORT` or `SERVICE_PORT` or default `8002`
- Binding to: `0.0.0.0:8080` ✅ CORRECT

### 6. **Memory/Resource Exhaustion**
- **Symptom**: Container OOM killed or throttled
- **Cause**: OCR models use too much memory

**Mitigations:**
- Using CPU-only PyTorch (smaller)
- Lazy loading OCR models (not loaded at startup)
- Single worker process (no duplication)

## What to Check in New Deployment Logs

Look for these key indicators:

### ✅ **Success Indicators:**
```
[DEBUG] Files in /app: [...]
[DEBUG] Resources exists: True
[DEBUG] Resources contents: ['card_mappings_final.csv', ...]
✓ Card matcher initialized successfully: 322 cards loaded
✓ FastAPI application loaded successfully
✓ Ready to accept connections on 0.0.0.0:8080
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### ❌ **Failure Indicators:**
```
❌ Failed to initialize card matcher: [error details]
❌ CRITICAL: Failed to load application: [error details]
[ERROR] Server failed with exception: [error details]
```

### 🔍 **What to Look For:**

1. **Does the service fully start?**
   - Should see "✓ Ready to accept connections"
   - Should see "INFO: Uvicorn running"

2. **Does the matcher load?**
   - Should see "✓ Card matcher initialized successfully: 322 cards loaded"
   - If not, check resources directory exists

3. **Do health checks succeed?**
   - Should see "GET /health HTTP/1.1 200 OK"
   - Should see "GET /api/v1/health HTTP/1.1 200 OK"

4. **Does the service stay alive?**
   - Should continue responding to multiple requests
   - Should NOT see "connection refused" after first request

## Emergency Fixes

### If service keeps crashing:

**Option 1: Minimal Health-Only Mode**
Comment out matcher initialization in `src/api/routes.py`:
```python
# matcher = CardMatcher(settings.card_mapping_path)
matcher = None  # Skip initialization
```

**Option 2: Increase Health Check Delays**
In `railway.toml`:
```toml
initialDelaySeconds = 60  # Give more time to start
periodSeconds = 60        # Check less frequently
failureThreshold = 5      # More tolerance
```

**Option 3: Check Railway Logs for Memory Issues**
Look for "OOMKilled" or memory warnings in Railway dashboard.

## Testing the Deployment

Once deployed, test these endpoints in order:

1. **Root endpoint**: `GET https://riftboundocr-production.up.railway.app/`
   - Should return service info

2. **Simple health check**: `GET https://riftboundocr-production.up.railway.app/health`
   - Should return `{"status": "healthy", ...}`

3. **Detailed health check**: `GET https://riftboundocr-production.up.railway.app/api/v1/health`
   - Should return full health info with matcher status

4. **Stats endpoint**: `GET https://riftboundocr-production.up.railway.app/api/v1/stats`
   - Should return service statistics

If ALL of these fail with 502, the service is definitely crashing. Check logs for error details.

## Next Steps

1. **Wait for new deployment** (pushed commit e6ec4fb)
2. **Monitor Railway deploy logs** for the new debug output
3. **Test health check endpoints** once deployed
4. **Report back** with:
   - Deploy logs (full output)
   - Health check responses
   - Any new error messages

---

**Changes Made:**
- commit e6ec4fb: Added comprehensive debugging and resilient health checks
- commit 44e636a: Added graceful shutdown, proper timeouts, and root /health endpoint
- commit c3980d5: Fixed duplicate section removal in parser

