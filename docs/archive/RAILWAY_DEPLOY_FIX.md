# Railway Deployment Fix ✅

## 🐛 Problem

Railway build was failing with error:
```
E: Package 'libgl1-mesa-glx' has no installation candidate
```

## 🔍 Root Cause

The Dockerfile used `libgl1-mesa-glx` which has been **deprecated** in newer Debian versions (Trixie). The Python 3.10-slim base image now uses Debian Trixie.

## ✅ Solution

Updated `Dockerfile` with modern package names:

### Changed:
```dockerfile
# OLD - Deprecated packages
libgl1-mesa-glx      # ❌ Not available in Debian Trixie
libxrender-dev       # ❌ Development package not needed
libgthread-2.0-0     # ❌ Deprecated

# NEW - Modern equivalents
libgl1               # ✅ Replacement for libgl1-mesa-glx
libxrender1          # ✅ Runtime library (not -dev)
# libgthread removed  # ✅ No longer needed
```

### Full Updated Package List:
```dockerfile
RUN apt-get update && apt-get install -y \
    libgl1 \            # OpenGL support (was libgl1-mesa-glx)
    libglib2.0-0 \      # GLib library
    libsm6 \            # Session management
    libxext6 \          # X extensions
    libxrender1 \       # X rendering (was libxrender-dev)
    libgomp1 \          # OpenMP support
    && rm -rf /var/lib/apt/lists/*
```

## 🚀 Deploy Now

```bash
# Commit the fix
git add Dockerfile
git commit -m "Fix Dockerfile for Debian Trixie compatibility"
git push

# Railway will auto-deploy
```

Or redeploy manually:
```bash
railway up
```

## ✅ Expected Result

Build should now succeed through all stages:
1. ✅ Base image pull
2. ✅ System dependencies install
3. ✅ Python packages install
4. ✅ Application copy
5. ✅ Container start

## 🔍 Verify Deployment

Once deployed:
```bash
# Get your Railway URL
railway domain

# Test health
curl https://your-app.railway.app/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "RiftboundOCR Service",
  "version": "1.0.0",
  "matcher_loaded": true,
  "total_cards_in_db": 322
}
```

## 📝 Other Changes Made

1. **Healthcheck:** Updated to use `urllib.request` instead of `requests` (which isn't in requirements.txt)
2. **Package cleanup:** Removed deprecated/unnecessary packages

## 💡 Why This Happened

Python base images are updated regularly. The `python:3.10-slim` image recently moved from Debian Bullseye to Debian Trixie, which removed some deprecated packages.

## 🎯 Alternative Solution (If Still Having Issues)

If you still encounter package issues, you can pin to an older Debian version:

```dockerfile
FROM python:3.10-slim-bullseye  # Uses older Debian (has libgl1-mesa-glx)
```

But the modern package names are recommended for long-term compatibility.

---

**Status:** ✅ Fixed and ready to deploy

