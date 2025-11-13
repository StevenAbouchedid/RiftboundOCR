# Frontend Integration Guide

## ✅ Service is Live!

Your OCR service is now deployed and accessible at:
```
https://riftboundocr-production.up.railway.app
```

## 🔧 Frontend Configuration

### 1. Base URL Setup

Configure your frontend with the correct base URL:

```javascript
// In your frontend config or .env file
const OCR_SERVICE_BASE_URL = 'https://riftboundocr-production.up.railway.app/api/v1';
```

**IMPORTANT:** Notice the `/api/v1` prefix! All OCR endpoints require this.

### 2. Health Check Endpoint

For checking if the service is available:

```javascript
// Simple health check (no /api/v1 prefix needed)
const checkHealth = async () => {
  try {
    const response = await axios.get(
      'https://riftboundocr-production.up.railway.app/health',
      { timeout: 5000 }
    );
    console.log('OCR service is healthy:', response.data);
    return true;
  } catch (error) {
    console.error('OCR service unavailable:', error);
    return false;
  }
};
```

### 3. Process Single Image

For uploading and processing a decklist image:

```javascript
const processImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await axios.post(
      'https://riftboundocr-production.up.railway.app/api/v1/process',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 120000  // 2 minutes - OCR takes time!
      }
    );
    
    return response.data;  // Contains parsed decklist
  } catch (error) {
    console.error('OCR processing failed:', error);
    throw error;
  }
};
```

### 4. Process Multiple Images with Progress (Recommended)

For batch processing with real-time progress updates:

```javascript
const processBatchWithProgress = async (files, onProgress, onResult, onComplete) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  try {
    const response = await fetch(
      'https://riftboundocr-production.up.railway.app/api/v1/process-batch-stream',
      {
        method: 'POST',
        body: formData
      }
    );
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n\n');
      
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          const eventMatch = line.match(/event: (\w+)\ndata: (.+)/s);
          if (eventMatch) {
            const [, eventType, dataStr] = eventMatch;
            const data = JSON.parse(dataStr);
            
            switch (eventType) {
              case 'progress':
                onProgress(data);  // { current, total, filename, status }
                break;
              case 'result':
                onResult(data);    // { index, filename, decklist }
                break;
              case 'complete':
                onComplete(data);  // { total, successful, failed, average_accuracy }
                break;
              case 'error':
                console.error('Processing error:', data);
                break;
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('Batch processing failed:', error);
    throw error;
  }
};

// Usage example
await processBatchWithProgress(
  selectedFiles,
  (progress) => {
    console.log(`Processing ${progress.current}/${progress.total}: ${progress.filename}`);
    updateProgressBar(progress);
  },
  (result) => {
    console.log(`Completed: ${result.filename}`);
    addDeckToList(result.decklist);
  },
  (summary) => {
    console.log(`Done! ${summary.successful}/${summary.total} successful`);
    showCompletionMessage(summary);
  }
);
```

## 📋 Available Endpoints

### Health & Info
- `GET /health` - Simple health check
- `GET /` - Service information
- `GET /api/v1/health` - Detailed health with matcher status
- `GET /api/v1/stats` - Service statistics

### OCR Processing
- `POST /api/v1/process` - Process single image
- `POST /api/v1/process-batch` - Process multiple images (returns when all complete)
- `POST /api/v1/process-batch-stream` - Process multiple with real-time progress (SSE)

## ⏱️ Timeout Settings

**CRITICAL:** OCR processing is slow! Set appropriate timeouts:

```javascript
// Health checks - fast
timeout: 5000  // 5 seconds

// Single image processing - slow
timeout: 120000  // 2 minutes (120 seconds)

// Batch processing - very slow
timeout: 300000  // 5 minutes (300 seconds)
// OR use streaming endpoint which doesn't need timeout
```

## 🔒 CORS Configuration

✅ **CORS is configured to allow all origins** - your frontend at `https://riftboundtopdecks.com` will work!

If you still see CORS errors after the latest deployment:
1. Make sure you're using the updated service (wait for Railway deployment to complete)
2. Check browser console for the exact error
3. Verify the request URL is correct (with `/api/v1/` prefix for processing endpoints)

## 📦 Response Format

### Single Image Response (`/api/v1/process`)

```json
{
  "decklist_id": "550e8400-e29b-41d4-a716-446655440000",
  "legend": [
    {
      "chinese_name": "火焰龙",
      "english_name": "Flame Dragon",
      "card_id": "12345",
      "quantity": 1,
      "confidence": 0.95
    }
  ],
  "main_deck": [...],
  "battlefields": [...],
  "runes": [...],
  "side_deck": [...],
  "stats": {
    "total_cards": 60,
    "total_matched": 58,
    "accuracy": 96.67,
    "processing_time_seconds": 45.2
  }
}
```

## 🐛 Common Issues & Fixes

### Issue: "No 'Access-Control-Allow-Origin' header"
**Fix:** Wait for latest deployment (CORS fix pushed). Clear browser cache.

### Issue: "404 Not Found"
**Fix:** Make sure you're using `/api/v1/process`, not `/process`

### Issue: "Request timeout"
**Fix:** Increase timeout to 120 seconds (2 minutes) for OCR processing

### Issue: "Network Error"
**Fix:** Check that service is healthy by visiting `/health` endpoint directly

## 🧪 Testing

Test the service is working:

```bash
# Health check
curl https://riftboundocr-production.up.railway.app/health

# Process an image
curl -X POST https://riftboundocr-production.up.railway.app/api/v1/process \
  -F "file=@test-image.jpg"
```

## 📊 Monitoring

Monitor your service health:
- **Railway Dashboard:** Check Metrics tab for uptime, memory, CPU
- **HTTP Logs:** View all requests and response codes
- **Deploy Logs:** See service health and keep-alive messages

---

## ✅ Quick Checklist

- [ ] Update frontend base URL to include `/api/v1`
- [ ] Set timeout to 120+ seconds for OCR requests
- [ ] Test health check endpoint works
- [ ] Test single image upload
- [ ] Test batch upload (if using)
- [ ] Handle errors gracefully in UI
- [ ] Show processing progress to users

**Your OCR service is ready to use!** 🎉

