# Streaming Batch Processing - Frontend Integration Guide

**Complete guide for integrating Server-Sent Events (SSE) streaming with your frontend.**

---

## Overview

The `/process-batch-stream` endpoint enables real-time progress updates and progressive results for batch image processing. Instead of waiting for all images to complete, your frontend receives results **immediately** as each image finishes processing.

###Benefits
- ✅ **Immediate feedback** - See progress bars and results in real-time
- ✅ **Better UX** - Users can start working on completed decklists while others process
- ✅ **No waiting** - Don't wait 5-10 minutes for entire batch
- ✅ **Resilient** - Errors don't break the stream

---

## Event Types

The endpoint streams four types of events:

### 1. `progress` Event
Sent during validation and processing of each image.

```json
{
  "current": 3,
  "total": 10,
  "filename": "deck3.jpg",
  "status": "processing"
}
```

**Fields:**
- `current` (int): Current image number (1-indexed)
- `total` (int): Total images in batch
- `filename` (string): Current file being processed
- `status` (string): Either `"validating"` or `"processing"`

### 2. `result` Event
Sent when an image successfully completes processing.

```json
{
  "index": 2,
  "filename": "deck3.jpg",
  "decklist": {
    "decklist_id": "uuid",
    "metadata": {"placement": 92, "event": "..."},
    "legend": [...],
    "main_deck": [...],
    "battlefields": [...],
    "runes": [...],
    "side_deck": [...],
    "stats": {
      "total_cards": 63,
      "matched_cards": 59,
      "accuracy": 93.65
    }
  }
}
```

**Fields:**
- `index` (int): Zero-based index of the image
- `filename` (string): Filename that was processed
- `decklist` (object): Complete decklist data (same as `/process` response)

### 3. `error` Event
Sent when an image fails validation or processing.

```json
{
  "index": 5,
  "filename": "deck6.jpg",
  "error": "File size (15.2MB) exceeds maximum (10MB)",
  "error_type": "validation"
}
```

**Fields:**
- `index` (int): Zero-based index of the failed image
- `filename` (string): Filename that failed
- `error` (string): Error message
- `error_type` (string): Either `"validation"` or `"processing"`

### 4. `complete` Event
Sent once at the end with final statistics.

```json
{
  "total": 10,
  "successful": 8,
  "failed": 2,
  "average_accuracy": 93.2,
  "processing_time_seconds": 245.5
}
```

**Fields:**
- `total` (int): Total images submitted
- `successful` (int): Successfully processed images
- `failed` (int): Failed images
- `average_accuracy` (float | null): Average accuracy across successful images
- `processing_time_seconds` (float): Total processing time

---

## Frontend Implementation

### JavaScript/Fetch API

**Basic Implementation:**

```javascript
async function processBatchWithProgress(files) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const response = await fetch('http://localhost:8080/api/process-batch-stream', {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    // Decode chunk and add to buffer
    buffer += decoder.decode(value, { stream: true });
    
    // Split by double newline (SSE event separator)
    const lines = buffer.split('\n\n');
    
    // Keep incomplete event in buffer
    buffer = lines.pop();
    
    // Process each complete event
    for (const line of lines) {
      if (!line.trim()) continue;
      
      // Parse SSE format: "event: <type>\ndata: <json>"
      const [eventLine, dataLine] = line.split('\n');
      
      if (!eventLine || !dataLine) continue;
      
      const eventType = eventLine.replace('event: ', '').trim();
      const eventData = JSON.parse(dataLine.replace('data: ', ''));
      
      // Handle event
      handleEvent(eventType, eventData);
    }
  }
}

function handleEvent(type, data) {
  switch (type) {
    case 'progress':
      console.log(`Processing ${data.current}/${data.total}: ${data.filename}`);
      updateProgressBar(data.current, data.total);
      break;
      
    case 'result':
      console.log(`Completed: ${data.filename}`, data.decklist);
      displayDecklist(data.decklist);
      break;
      
    case 'error':
      console.error(`Failed: ${data.filename} - ${data.error}`);
      showErrorNotification(data);
      break;
      
    case 'complete':
      console.log('Batch complete!', data);
      showCompletionSummary(data);
      break;
  }
}
```

**With Callbacks:**

```javascript
async function processBatchWithCallbacks(files, callbacks) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const response = await fetch('http://localhost:8080/api/process-batch-stream', {
    method: 'POST',
    body: formData
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop();
    
    for (const line of lines) {
      if (!line.trim()) continue;
      
      const [eventLine, dataLine] = line.split('\n');
      const eventType = eventLine.replace('event: ', '').trim();
      const eventData = JSON.parse(dataLine.replace('data: ', ''));
      
      // Call appropriate callback
      const callback = callbacks[eventType];
      if (callback) callback(eventData);
    }
  }
}

// Usage
const results = [];
const errors = [];

await processBatchWithCallbacks(imageFiles, {
  progress: (data) => {
    console.log(`Progress: ${data.current}/${data.total}`);
    document.getElementById('progress').textContent = 
      `${data.current}/${data.total}`;
  },
  
  result: (data) => {
    results.push(data.decklist);
    appendDecklistToUI(data.decklist);
  },
  
  error: (data) => {
    errors.push(data);
    showError(data.filename, data.error);
  },
  
  complete: (data) => {
    console.log(`Done: ${data.successful}/${data.total} successful`);
    alert(`Processing complete! ${data.successful} successful, ${data.failed} failed`);
  }
});
```

---

### React Component Example

**Complete React Component with Hooks:**

```jsx
import React, { useState, useCallback } from 'react';
import './BatchUploader.css';

function BatchUploader() {
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [results, setResults] = useState([]);
  const [errors, setErrors] = useState([]);
  const [summary, setSummary] = useState(null);
  
  const handleFileChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(selectedFiles);
    // Reset state
    setResults([]);
    setErrors([]);
    setSummary(null);
    setProgress({ current: 0, total: 0 });
  };
  
  const processFiles = useCallback(async () => {
    if (files.length === 0) return;
    
    setProcessing(true);
    setProgress({ current: 0, total: files.length });
    
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    try {
      const response = await fetch('http://localhost:8080/api/process-batch-stream', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop();
        
        for (const line of lines) {
          if (!line.trim()) continue;
          
          const [eventLine, dataLine] = line.split('\n');
          if (!eventLine || !dataLine) continue;
          
          const eventType = eventLine.replace('event: ', '').trim();
          const eventData = JSON.parse(dataLine.replace('data: ', ''));
          
          // Handle each event type
          switch (eventType) {
            case 'progress':
              setProgress({
                current: eventData.current,
                total: eventData.total
              });
              break;
              
            case 'result':
              setResults(prev => [...prev, eventData.decklist]);
              break;
              
            case 'error':
              setErrors(prev => [...prev, eventData]);
              break;
              
            case 'complete':
              setSummary(eventData);
              break;
          }
        }
      }
    } catch (error) {
      console.error('Stream processing failed:', error);
      alert('Processing failed: ' + error.message);
    } finally {
      setProcessing(false);
    }
  }, [files]);
  
  const progressPercent = progress.total > 0 
    ? (progress.current / progress.total) * 100 
    : 0;
  
  return (
    <div className="batch-uploader">
      <h2>Batch Decklist Upload</h2>
      
      {/* File Input */}
      <div className="upload-section">
        <input
          type="file"
          multiple
          accept="image/*"
          onChange={handleFileChange}
          disabled={processing}
        />
        <button 
          onClick={processFiles} 
          disabled={processing || files.length === 0}
        >
          {processing ? 'Processing...' : `Process ${files.length} Images`}
        </button>
      </div>
      
      {/* Progress Bar */}
      {processing && (
        <div className="progress-section">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <p className="progress-text">
            Processing: {progress.current} / {progress.total}
          </p>
        </div>
      )}
      
      {/* Results */}
      {results.length > 0 && (
        <div className="results-section">
          <h3>Results ({results.length})</h3>
          <div className="results-grid">
            {results.map((decklist, idx) => (
              <DecklistCard 
                key={decklist.decklist_id} 
                decklist={decklist} 
              />
            ))}
          </div>
        </div>
      )}
      
      {/* Errors */}
      {errors.length > 0 && (
        <div className="errors-section">
          <h3>Errors ({errors.length})</h3>
          {errors.map((error, idx) => (
            <div key={idx} className="error-item">
              <strong>{error.filename}:</strong> {error.error}
            </div>
          ))}
        </div>
      )}
      
      {/* Summary */}
      {summary && (
        <div className="summary-section">
          <h3>Processing Complete</h3>
          <div className="summary-stats">
            <p><strong>Total:</strong> {summary.total}</p>
            <p><strong>Successful:</strong> {summary.successful}</p>
            <p><strong>Failed:</strong> {summary.failed}</p>
            {summary.average_accuracy && (
              <p><strong>Avg Accuracy:</strong> {summary.average_accuracy.toFixed(2)}%</p>
            )}
            <p><strong>Time:</strong> {summary.processing_time_seconds}s</p>
          </div>
        </div>
      )}
    </div>
  );
}

function DecklistCard({ decklist }) {
  const totalCards = (
    decklist.legend.length +
    decklist.main_deck.length +
    decklist.battlefields.length +
    decklist.runes.length +
    decklist.side_deck.length
  );
  
  return (
    <div className="decklist-card">
      <h4>{decklist.metadata.event || 'Decklist'}</h4>
      <p>ID: {decklist.decklist_id}</p>
      <p>Total Cards: {totalCards}</p>
      {decklist.stats && (
        <p>Accuracy: {decklist.stats.accuracy.toFixed(2)}%</p>
      )}
      <button onClick={() => viewDecklist(decklist)}>
        View Details
      </button>
    </div>
  );
}

export default BatchUploader;
```

**CSS (BatchUploader.css):**

```css
.batch-uploader {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.upload-section {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.upload-section button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.upload-section button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.progress-section {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 30px;
  background: #f0f0f0;
  border-radius: 15px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #45a049);
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

.progress-text {
  text-align: center;
  font-size: 16px;
  color: #666;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 15px;
}

.decklist-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.decklist-card h4 {
  margin-top: 0;
  color: #333;
}

.decklist-card button {
  width: 100%;
  padding: 8px;
  margin-top: 10px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.errors-section {
  margin-top: 20px;
  padding: 15px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
}

.error-item {
  margin: 10px 0;
  color: #856404;
}

.summary-section {
  margin-top: 20px;
  padding: 15px;
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
}

.summary-stats p {
  margin: 5px 0;
}
```

---

### Vue.js Example

```vue
<template>
  <div class="batch-uploader">
    <h2>Batch Decklist Upload</h2>
    
    <div class="upload-section">
      <input
        type="file"
        multiple
        accept="image/*"
        @change="handleFileChange"
        :disabled="processing"
        ref="fileInput"
      />
      <button @click="processFiles" :disabled="processing || files.length === 0">
        {{ processing ? 'Processing...' : `Process ${files.length} Images` }}
      </button>
    </div>
    
    <div v-if="processing" class="progress-section">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <p>Processing: {{ progress.current }} / {{ progress.total }}</p>
    </div>
    
    <div v-if="results.length > 0" class="results-section">
      <h3>Results ({{ results.length }})</h3>
      <div class="results-grid">
        <div v-for="decklist in results" :key="decklist.decklist_id" class="decklist-card">
          <h4>{{ decklist.metadata.event || 'Decklist' }}</h4>
          <p>Accuracy: {{ decklist.stats?.accuracy.toFixed(2) }}%</p>
        </div>
      </div>
    </div>
    
    <div v-if="errors.length > 0" class="errors-section">
      <h3>Errors ({{ errors.length }})</h3>
      <div v-for="(error, idx) in errors" :key="idx" class="error-item">
        <strong>{{ error.filename }}:</strong> {{ error.error }}
      </div>
    </div>
    
    <div v-if="summary" class="summary-section">
      <h3>Complete!</h3>
      <p>Successful: {{ summary.successful }} / {{ summary.total }}</p>
      <p v-if="summary.average_accuracy">
        Avg Accuracy: {{ summary.average_accuracy.toFixed(2) }}%
      </p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      files: [],
      processing: false,
      progress: { current: 0, total: 0 },
      results: [],
      errors: [],
      summary: null
    };
  },
  computed: {
    progressPercent() {
      return this.progress.total > 0 
        ? (this.progress.current / this.progress.total) * 100 
        : 0;
    }
  },
  methods: {
    handleFileChange(event) {
      this.files = Array.from(event.target.files);
      this.results = [];
      this.errors = [];
      this.summary = null;
    },
    
    async processFiles() {
      if (this.files.length === 0) return;
      
      this.processing = true;
      this.progress = { current: 0, total: this.files.length };
      
      const formData = new FormData();
      this.files.forEach(file => formData.append('files', file));
      
      try {
        const response = await fetch('http://localhost:8080/api/process-batch-stream', {
          method: 'POST',
          body: formData
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop();
          
          for (const line of lines) {
            if (!line.trim()) continue;
            
            const [eventLine, dataLine] = line.split('\n');
            if (!eventLine || !dataLine) continue;
            
            const eventType = eventLine.replace('event: ', '').trim();
            const eventData = JSON.parse(dataLine.replace('data: ', ''));
            
            this.handleEvent(eventType, eventData);
          }
        }
      } catch (error) {
        console.error('Processing failed:', error);
        alert('Processing failed: ' + error.message);
      } finally {
        this.processing = false;
      }
    },
    
    handleEvent(type, data) {
      switch (type) {
        case 'progress':
          this.progress = { current: data.current, total: data.total };
          break;
        case 'result':
          this.results.push(data.decklist);
          break;
        case 'error':
          this.errors.push(data);
          break;
        case 'complete':
          this.summary = data;
          break;
      }
    }
  }
};
</script>
```

---

## Testing with cURL

**Basic SSE stream test:**

```bash
curl -X POST http://localhost:8080/api/process-batch-stream \
  -F "files=@deck1.jpg" \
  -F "files=@deck2.jpg" \
  -N --no-buffer
```

**Output:**
```
event: progress
data: {"current":1,"total":2,"filename":"deck1.jpg","status":"validating"}

event: progress
data: {"current":1,"total":2,"filename":"deck1.jpg","status":"processing"}

event: result
data: {"index":0,"filename":"deck1.jpg","decklist":{...}}

event: progress
data: {"current":2,"total":2,"filename":"deck2.jpg","status":"validating"}

event: progress
data: {"current":2,"total":2,"filename":"deck2.jpg","status":"processing"}

event: result
data: {"index":1,"filename":"deck2.jpg","decklist":{...}}

event: complete
data: {"total":2,"successful":2,"failed":0,"average_accuracy":95.3,"processing_time_seconds":87.5}
```

---

## Error Handling

### Network Errors

```javascript
try {
  await processBatchWithProgress(files);
} catch (error) {
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    console.error('Network error - is server running?');
  } else {
    console.error('Unexpected error:', error);
  }
}
```

### HTTP Errors

```javascript
const response = await fetch('http://localhost:8080/api/process-batch-stream', {
  method: 'POST',
  body: formData
});

if (!response.ok) {
  const error = await response.json();
  throw new Error(`Server error: ${error.detail || response.statusText}`);
}
```

### Stream Interruption

```javascript
let lastEventTime = Date.now();

// In your event loop:
for (const line of lines) {
  lastEventTime = Date.now();
  // ... process event
}

// Check for timeout
if (Date.now() - lastEventTime > 60000) {
  console.error('Stream timeout - no events for 60s');
  reader.cancel();
}
```

---

## Best Practices

### 1. Show Real-Time Feedback
```javascript
// Update UI immediately on progress events
case 'progress':
  updateProgressBar(data.current, data.total);
  updateStatusText(`Processing ${data.filename}...`);
  break;
```

### 2. Enable User Interaction During Processing
```javascript
// Users can start working on completed decklists
case 'result':
  const decklist = data.decklist;
  addDecklistToUI(decklist, { 
    editable: true,  // Allow editing while others process
    status: 'ready'
  });
  break;
```

### 3. Handle Partial Success
```javascript
case 'complete':
  if (data.failed > 0) {
    showWarning(`${data.failed} images failed. Check errors below.`);
  }
  if (data.successful > 0) {
    showSuccess(`${data.successful} decklists processed!`);
  }
  break;
```

### 4. Provide Retry Options
```javascript
case 'error':
  showError({
    message: `Failed: ${data.filename}`,
    detail: data.error,
    retry: () => retryImage(data.filename)
  });
  break;
```

### 5. Save Results Incrementally
```javascript
case 'result':
  // Save to local storage immediately
  saveToLocalStorage(data.decklist);
  
  // Or send to your backend
  await saveToDatabase(data.decklist);
  break;
```

---

## Browser Compatibility

SSE (Server-Sent Events) via Fetch API is supported in:
- ✅ Chrome 85+
- ✅ Firefox 80+
- ✅ Safari 14+
- ✅ Edge 85+

For older browsers, fallback to regular `/process-batch` endpoint.

**Feature Detection:**

```javascript
if (!('ReadableStream' in window)) {
  console.warn('ReadableStream not supported, using fallback');
  // Use /process-batch instead
  return await processB atchFallback(files);
}
```

---

## Performance Tips

1. **Batch Size**: Keep batches under 10 images for best experience
2. **Parallel Display**: Update UI as events arrive (don't wait for all)
3. **Memory**: Clear old results if processing many batches
4. **Feedback**: Always show progress - processing takes 30-60s per image

---

## Troubleshooting

### Events Not Streaming

**Problem:** All events arrive at once instead of progressively.

**Solution:** Check nginx/proxy configuration:
```nginx
location /api/ {
    proxy_buffering off;
    proxy_set_header X-Accel-Buffering no;
}
```

### JSON Parse Errors

**Problem:** `JSON.parse()` fails on event data.

**Solution:** Ensure you're correctly splitting SSE format:
```javascript
// Correct: split by "\n\n" first
const events = buffer.split('\n\n');

// Then parse each event
const [eventLine, dataLine] = event.split('\n');
```

### Missing Events

**Problem:** Some events don't appear.

**Solution:** Check buffer handling:
```javascript
// Always keep incomplete event in buffer
const lines = buffer.split('\n\n');
buffer = lines.pop();  // ← Important!
```

---

## Next Steps

- ✅ Implement SSE client in your frontend
- ✅ Add progress bars and real-time updates
- ✅ Test with multiple images
- ✅ Handle errors gracefully
- 🚀 Deploy and enjoy instant feedback!

**Questions?** Check the main API documentation or open an issue!


