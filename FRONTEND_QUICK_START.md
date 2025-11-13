# OCR Service - Frontend Quick Start

## 🚀 Service URL

```
https://riftboundocr-production.up.railway.app
```

## ⚡ Quick Setup

### 1. Configuration

```javascript
// Add to your .env or config
const OCR_SERVICE_URL = 'https://riftboundocr-production.up.railway.app/api/v1';
```

### 2. Health Check

```javascript
// Check if service is available
const response = await fetch('https://riftboundocr-production.up.railway.app/health');
const data = await response.json();
// { status: "healthy", service: "RiftboundOCR Service", version: "1.0.0" }
```

### 3. Upload & Process Image

```javascript
const processImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  const response = await fetch(
    'https://riftboundocr-production.up.railway.app/api/v1/process',
    {
      method: 'POST',
      body: formData,
      // IMPORTANT: 2 minute timeout for OCR processing
      signal: AbortSignal.timeout(120000)
    }
  );
  
  if (!response.ok) {
    throw new Error(`OCR failed: ${response.status}`);
  }
  
  return await response.json();
};

// Usage
const result = await processImage(file);
console.log('Parsed decklist:', result);
```

### 4. Using Axios (Alternative)

```javascript
import axios from 'axios';

const processImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  const response = await axios.post(
    'https://riftboundocr-production.up.railway.app/api/v1/process',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000  // 2 minutes
    }
  );
  
  return response.data;
};
```

## 📋 Response Format

```javascript
{
  "decklist_id": "uuid-here",
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

## 🔑 Key Points

1. **Base URL:** Use `/api/v1` prefix for all processing endpoints
2. **Timeout:** Set to 120 seconds (2 minutes) - OCR is slow!
3. **File Type:** JPG or PNG images only
4. **Max Size:** 10MB per image
5. **CORS:** Already configured for `https://riftboundtopdecks.com`

## 🎯 Common Mistakes

### ❌ Wrong URL (Missing /api/v1)
```javascript
POST /process  // 404 Error
```

### ✅ Correct URL
```javascript
POST /api/v1/process  // Works!
```

### ❌ Timeout Too Short
```javascript
timeout: 5000  // Will timeout before OCR completes
```

### ✅ Correct Timeout
```javascript
timeout: 120000  // 2 minutes - works!
```

## 🧪 Test Commands

```bash
# Health check
curl https://riftboundocr-production.up.railway.app/health

# Process image
curl -X POST https://riftboundocr-production.up.railway.app/api/v1/process \
  -F "file=@test-image.jpg" \
  --max-time 120
```

## 🆘 Troubleshooting

| Error | Fix |
|-------|-----|
| 404 Not Found | Add `/api/v1` prefix to URL |
| Timeout | Increase timeout to 120 seconds |
| CORS Error | Wait for latest deployment (fix pushed) |
| 502 Bad Gateway | Service is restarting, retry in 30s |

## 📞 Need Help?

- Check service health: `https://riftboundocr-production.up.railway.app/health`
- View full API docs: `https://riftboundocr-production.up.railway.app/docs`
- See detailed guide: `FRONTEND_INTEGRATION.md`

---

**That's it!** Copy the code above and update your URLs. 🎉

