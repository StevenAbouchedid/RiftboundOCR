# Frontend Streaming Integration Guide

## ⚠️ CRITICAL FIX REQUIRED

Your frontend is currently using `/api/v1/process` which has a **120-second client timeout** and **no progress updates**. This causes timeouts on first requests when EasyOCR is downloading models (20-30 seconds).

## The Solution: Use Streaming Endpoint

Switch to `/api/v1/process-stream` which:
- ✅ Streams progress updates (no blind waiting)
- ✅ Keeps connection alive (prevents timeouts)
- ✅ Better UX with progress bar
- ✅ Handles long OCR processing gracefully

---

## API Change Required

### ❌ OLD (Don't Use)
```javascript
POST /api/v1/process
// Returns JSON after 20-120 seconds
// Frontend times out after 120s
// No progress updates
```

### ✅ NEW (Use This)
```javascript
POST /api/v1/process-stream
// Returns Server-Sent Events (SSE)
// Streams progress updates every few seconds
// No timeout issues
```

---

## Implementation Examples

### Option 1: Using EventSource (Recommended)

```javascript
async function processImageStreaming(file) {
  const formData = new FormData();
  formData.append('file', file);

  // Upload file and get stream URL
  const response = await fetch('https://riftboundocr-production.up.railway.app/api/v1/process-stream', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // Read SSE stream
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let result = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop(); // Keep incomplete message

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.event === 'progress') {
          console.log(`Progress: ${data.data.progress}% - ${data.data.message}`);
          // Update your progress bar here
        } else if (data.event === 'result') {
          result = data.data;
          console.log('OCR Complete!', result);
        } else if (data.event === 'error') {
          throw new Error(data.data.message);
        }
      }
    }
  }

  return result;
}
```

### Option 2: Using fetch with ReadableStream

```javascript
async function processImageWithProgress(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('https://riftboundocr-production.up.railway.app/api/v1/process-stream', {
    method: 'POST',
    body: formData
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalResult = null;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop();

      for (const event of events) {
        const match = event.match(/data: (.+)/);
        if (match) {
          const data = JSON.parse(match[1]);
          
          switch (data.event) {
            case 'progress':
              onProgress?.(data.data);
              break;
            case 'result':
              finalResult = data.data;
              break;
            case 'error':
              throw new Error(data.data.message);
            case 'complete':
              return finalResult;
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return finalResult;
}

// Usage:
const result = await processImageWithProgress(file, (progress) => {
  console.log(`${progress.progress}%: ${progress.message}`);
  setProgress(progress.progress);
  setStatus(progress.message);
});
```

### Option 3: Simple React Hook

```typescript
import { useState, useCallback } from 'react';

interface ProgressData {
  status: string;
  message: string;
  progress: number;
}

export function useOCRStreaming() {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const processImage = useCallback(async (file: File) => {
    setIsProcessing(true);
    setError(null);
    setProgress(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(
        'https://riftboundocr-production.up.railway.app/api/v1/process-stream',
        {
          method: 'POST',
          body: formData
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const event of events) {
          const match = event.match(/data: (.+)/);
          if (match) {
            const data = JSON.parse(match[1]);

            if (data.event === 'progress') {
              setProgress(data.data);
            } else if (data.event === 'result') {
              setResult(data.data);
            } else if (data.event === 'error') {
              throw new Error(data.data.message);
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsProcessing(false);
    }
  }, []);

  return { processImage, progress, result, error, isProcessing };
}
```

---

## Event Types

The streaming endpoint sends these events:

### 1. `progress` Event
```json
{
  "event": "progress",
  "data": {
    "status": "starting" | "ocr" | "matching",
    "message": "Human-readable status message",
    "progress": 0-100
  }
}
```

### 2. `result` Event
```json
{
  "event": "result",
  "data": {
    "decklist_id": "uuid",
    "cards": { ... },
    "metadata": { ... },
    "stats": {
      "total_cards": 60,
      "accuracy": 95.5,
      "match_rate": 0.98
    }
  }
}
```

### 3. `error` Event
```json
{
  "event": "error",
  "data": {
    "error": "error type",
    "message": "Detailed error message"
  }
}
```

### 4. `complete` Event
```json
{
  "event": "complete",
  "data": {
    "status": "success",
    "progress": 100
  }
}
```

---

## Migration Steps

1. **Test the streaming endpoint** with the examples above
2. **Update your frontend** to use `/api/v1/process-stream`
3. **Add progress UI** to show users what's happening
4. **Remove the 120-second timeout** (streaming handles long requests)
5. **Test with both PC and mobile** to ensure it works everywhere

---

## Expected Timings

- **First request (cold start)**: 30-60 seconds
  - EasyOCR downloads models (~20-30s)
  - OCR processing (~10-20s)
  - You'll see progress updates throughout

- **Subsequent requests**: 10-20 seconds
  - Models are cached
  - Only OCR processing time

---

## Troubleshooting

### Still getting timeouts?
- Make sure you're using the streaming endpoint `/api/v1/process-stream`
- Check that you're reading the SSE stream properly
- Don't use Axios (it doesn't support SSE well)

### No progress updates?
- Check browser console for errors
- Make sure you're parsing the `data:` lines correctly
- SSE format is: `data: {json}\n\n`

### CORS errors?
- The endpoint supports CORS (all origins allowed)
- If you see CORS errors, check your request headers

---

## Questions?

The streaming endpoint is live at:
```
https://riftboundocr-production.up.railway.app/api/v1/process-stream
```

Test it with curl:
```bash
curl -X POST \
  https://riftboundocr-production.up.railway.app/api/v1/process-stream \
  -F "file=@image.jpg"
```

You should see progress events streaming in real-time!

