# Streaming Batch Processing - Implementation Plan

**Date**: November 12, 2025  
**Feature**: Real-time Progress Updates & Progressive Results for Batch Processing  
**Estimated Time**: 3-7 hours (depending on scope)

---

## Problem Statement

**Current State:**
- `/process-batch` endpoint processes all images sequentially
- Returns results only when entire batch completes
- Processing time: 30-60 seconds per image (10 images = 5-10 minutes)
- No progress visibility during processing
- Users must wait for complete batch before starting work

**User Impact:**
- Poor UX for time-sensitive workflows
- No feedback during long processing times
- Cannot start working on completed decklists while others process
- Frustrating wait times for bulk imports

---

## Proposed Solution

### Two-Phase Implementation

#### **Phase 8: Server-Sent Events (SSE) Streaming** ⭐ PRIORITY
Enable progressive results as they complete with real-time progress updates.

**Benefits:**
- ✅ Users see results immediately (no waiting for entire batch)
- ✅ Real-time progress bar (current/total)
- ✅ Can start working on first deck while others process
- ✅ Better UX with immediate feedback
- ✅ No new dependencies or infrastructure

**Estimated Time:** 3-4 hours

#### **Phase 9: Parallel Processing** 🚀 OPTIONAL
Process multiple images simultaneously to reduce total time.

**Benefits:**
- ⚡ 40-60% reduction in total processing time
- ⚡ Process 2-4 images concurrently
- ⚡ Better resource utilization

**Estimated Time:** 2-3 hours

---

## Technical Design

### Architecture Decision: Server-Sent Events (SSE)

**Why SSE over alternatives:**

| Solution | Pros | Cons | Verdict |
|----------|------|------|---------|
| **SSE** ✅ | Native browser support, simple, perfect for one-way updates | One-way only | **SELECTED** |
| WebSockets | Bi-directional, real-time | Overkill, more complex | Not needed |
| Polling | Simple, works everywhere | Inefficient, delayed | Fallback only |
| Job Queue | Production-grade, scalable | Requires Redis/RabbitMQ | Future upgrade |

**SSE is perfect for our use case:**
- Server pushes updates to client (one-way)
- Native `EventSource` API in browsers
- Automatic reconnection
- No additional infrastructure

---

## Phase 8: SSE Implementation

### 8.1 Core Endpoint Implementation

**New Endpoint:** `POST /api/process-batch-stream`

**Event Types:**

1. **Progress Event**
```json
event: progress
data: {
  "current": 3,
  "total": 10,
  "filename": "deck3.jpg",
  "status": "processing"
}
```

2. **Result Event**
```json
event: result
data: {
  "index": 2,
  "decklist": {
    "decklist_id": "uuid",
    "legend": [...],
    "main_deck": [...],
    "stats": {"accuracy": 95.5}
  }
}
```

3. **Error Event**
```json
event: error
data: {
  "index": 5,
  "filename": "deck5.jpg",
  "error": "Invalid file format"
}
```

4. **Complete Event**
```json
event: complete
data: {
  "total": 10,
  "successful": 8,
  "failed": 2,
  "average_accuracy": 93.2
}
```

### Implementation Code Structure

```python
# src/api/routes.py

from fastapi.responses import StreamingResponse
import json

@router.post("/process-batch-stream")
async def process_batch_stream(files: List[UploadFile] = File(...)):
    """
    Process multiple images with streaming results
    Returns Server-Sent Events (SSE) stream
    """
    
    async def event_generator():
        total = len(files)
        successful = 0
        failed = 0
        total_accuracy = 0.0
        
        for idx, file in enumerate(files):
            try:
                # Send progress event
                yield format_sse_event(
                    event="progress",
                    data={
                        "current": idx + 1,
                        "total": total,
                        "filename": file.filename,
                        "status": "processing"
                    }
                )
                
                # Validate and process image
                content = await file.read()
                # ... validation logic ...
                
                # Process with OCR
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                
                parsed = parser.parse(tmp_path)
                matched = matcher.match_decklist(parsed)
                matched['decklist_id'] = str(uuid.uuid4())
                
                # Send result event
                yield format_sse_event(
                    event="result",
                    data={
                        "index": idx,
                        "decklist": matched
                    }
                )
                
                successful += 1
                total_accuracy += matched.get('stats', {}).get('accuracy', 0)
                
                os.unlink(tmp_path)
                
            except Exception as e:
                # Send error event (don't break stream)
                yield format_sse_event(
                    event="error",
                    data={
                        "index": idx,
                        "filename": file.filename,
                        "error": str(e)
                    }
                )
                failed += 1
        
        # Send completion event
        avg_accuracy = (total_accuracy / successful) if successful > 0 else None
        yield format_sse_event(
            event="complete",
            data={
                "total": total,
                "successful": successful,
                "failed": failed,
                "average_accuracy": avg_accuracy
            }
        )
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # For nginx compatibility
            "Connection": "keep-alive"
        }
    )


def format_sse_event(event: str, data: dict) -> str:
    """Format data as Server-Sent Event"""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
```

### 8.2 Frontend Integration

**JavaScript/Fetch API Example:**

```javascript
async function processBatchWithProgress(files, onProgress, onResult, onError, onComplete) {
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
    buffer = lines.pop(); // Keep incomplete event
    
    for (const line of lines) {
      if (!line.trim()) continue;
      
      const [eventLine, dataLine] = line.split('\n');
      const eventType = eventLine.replace('event: ', '');
      const data = JSON.parse(dataLine.replace('data: ', ''));
      
      switch (eventType) {
        case 'progress':
          onProgress(data);
          break;
        case 'result':
          onResult(data);
          break;
        case 'error':
          onError(data);
          break;
        case 'complete':
          onComplete(data);
          break;
      }
    }
  }
}

// Usage Example
const results = [];

processBatchWithProgress(
  imageFiles,
  // Progress callback
  (progress) => {
    console.log(`Processing ${progress.current}/${progress.total}: ${progress.filename}`);
    updateProgressBar(progress.current, progress.total);
  },
  // Result callback
  (result) => {
    console.log(`Completed deck ${result.index}:`, result.decklist);
    results.push(result.decklist);
    displayDecklistInUI(result.decklist); // User can start working immediately!
  },
  // Error callback
  (error) => {
    console.error(`Failed to process ${error.filename}:`, error.error);
    showErrorNotification(error);
  },
  // Complete callback
  (summary) => {
    console.log(`Batch complete: ${summary.successful}/${summary.total} successful`);
    console.log(`Average accuracy: ${summary.average_accuracy}%`);
    showCompletionMessage(summary);
  }
);
```

**React Component Example:**

```jsx
import React, { useState } from 'react';

function BatchUploader() {
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [results, setResults] = useState([]);
  const [errors, setErrors] = useState([]);
  const [processing, setProcessing] = useState(false);
  
  const handleUpload = async (files) => {
    setProcessing(true);
    setResults([]);
    setErrors([]);
    
    await processBatchWithProgress(
      files,
      (prog) => setProgress(prog),
      (result) => setResults(prev => [...prev, result.decklist]),
      (error) => setErrors(prev => [...prev, error]),
      (summary) => {
        setProcessing(false);
        alert(`Complete! ${summary.successful}/${summary.total} successful`);
      }
    );
  };
  
  return (
    <div>
      <input 
        type="file" 
        multiple 
        accept="image/*"
        onChange={(e) => handleUpload(Array.from(e.target.files))}
        disabled={processing}
      />
      
      {processing && (
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${(progress.current / progress.total) * 100}%` }}
          />
          <span>{progress.current} / {progress.total}</span>
        </div>
      )}
      
      <div className="results-container">
        {results.map((decklist, idx) => (
          <DecklistCard key={decklist.decklist_id} decklist={decklist} />
        ))}
      </div>
      
      {errors.length > 0 && (
        <div className="errors">
          {errors.map((err, idx) => (
            <div key={idx} className="error-item">
              Failed: {err.filename} - {err.error}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 8.3 Testing Strategy

**Test Cases (`tests/test_streaming.py`):**

```python
import pytest
from fastapi.testclient import TestClient

def test_sse_connection_headers():
    """Test SSE response has correct headers"""
    response = client.post("/api/process-batch-stream", files=[...])
    assert response.headers["content-type"] == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache"

def test_progress_events():
    """Test progress events are emitted"""
    events = list(parse_sse_stream(response))
    progress_events = [e for e in events if e['event'] == 'progress']
    assert len(progress_events) == 3  # For 3 files

def test_result_events():
    """Test result events contain valid decklist data"""
    events = list(parse_sse_stream(response))
    result_events = [e for e in events if e['event'] == 'result']
    
    for result in result_events:
        assert 'decklist' in result['data']
        assert 'decklist_id' in result['data']['decklist']

def test_error_handling():
    """Test errors don't break the stream"""
    files = [valid_image, invalid_image, valid_image]
    events = list(parse_sse_stream(response))
    
    # Should have 2 results, 1 error, 1 complete
    assert len([e for e in events if e['event'] == 'result']) == 2
    assert len([e for e in events if e['event'] == 'error']) == 1
    assert len([e for e in events if e['event'] == 'complete']) == 1

def test_completion_event():
    """Test completion event has correct statistics"""
    events = list(parse_sse_stream(response))
    complete = [e for e in events if e['event'] == 'complete'][0]
    
    assert complete['data']['total'] == 5
    assert complete['data']['successful'] == 4
    assert complete['data']['failed'] == 1
    assert 'average_accuracy' in complete['data']
```

### 8.4 Documentation

**Files to Create/Update:**
- `docs/STREAMING_GUIDE.md` - Complete frontend integration guide
- `API_REFERENCE.md` - Add streaming endpoint documentation
- `README.md` - Update with streaming endpoint example

---

## Phase 9: Parallel Processing (Optional)

### 9.1 Configuration

Add to `src/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Parallel processing
    max_workers: int = Field(
        default=2,
        description="Maximum parallel workers for batch processing"
    )
    enable_parallel: bool = Field(
        default=False,
        description="Enable parallel processing (disable for GPU mode)"
    )
```

### 9.2 Implementation

**New Endpoint:** `POST /api/process-batch-fast`

```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

def process_single_image_sync(file_data: tuple) -> dict:
    """Worker function for parallel processing"""
    content, filename = file_data
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        parsed = parser.parse(tmp_path)
        matched = matcher.match_decklist(parsed)
        matched['decklist_id'] = str(uuid.uuid4())
        return {'success': True, 'result': matched, 'filename': filename}
    except Exception as e:
        return {'success': False, 'error': str(e), 'filename': filename}
    finally:
        os.unlink(tmp_path)


@router.post("/process-batch-fast")
async def process_batch_fast_stream(files: List[UploadFile] = File(...)):
    """Process with SSE streaming + parallel processing"""
    
    if not settings.enable_parallel:
        raise HTTPException(
            status_code=400,
            detail="Parallel processing not enabled (use /process-batch-stream instead)"
        )
    
    async def event_generator():
        # Read all files first
        file_data = [(await f.read(), f.filename) for f in files]
        total = len(file_data)
        processed = 0
        
        # Process in batches of N
        batch_size = settings.max_workers
        
        with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
            for i in range(0, len(file_data), batch_size):
                batch = file_data[i:i+batch_size]
                
                # Process batch in parallel
                loop = asyncio.get_event_loop()
                futures = [
                    loop.run_in_executor(executor, process_single_image_sync, data)
                    for data in batch
                ]
                
                results = await asyncio.gather(*futures)
                
                # Stream results
                for result in results:
                    processed += 1
                    
                    yield format_sse_event(
                        event="progress",
                        data={"current": processed, "total": total}
                    )
                    
                    if result['success']:
                        yield format_sse_event(
                            event="result",
                            data={"decklist": result['result']}
                        )
                    else:
                        yield format_sse_event(
                            event="error",
                            data={"filename": result['filename'], "error": result['error']}
                        )
        
        yield format_sse_event(event="complete", data={"total": total})
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 9.3 Performance Testing

**Benchmark Script:**

```python
import time

def benchmark_batch_processing():
    files = [test_image_1, test_image_2, ..., test_image_10]
    
    # Test sequential
    start = time.time()
    response = client.post("/api/process-batch")
    sequential_time = time.time() - start
    
    # Test streaming (still sequential)
    start = time.time()
    response = client.post("/api/process-batch-stream")
    # ... consume stream ...
    streaming_time = time.time() - start
    
    # Test parallel (2 workers)
    start = time.time()
    response = client.post("/api/process-batch-fast")
    # ... consume stream ...
    parallel_time = time.time() - start
    
    print(f"Sequential: {sequential_time:.2f}s")
    print(f"Streaming:  {streaming_time:.2f}s")
    print(f"Parallel:   {parallel_time:.2f}s")
    print(f"Speedup:    {(sequential_time / parallel_time):.1f}x")
```

---

## Implementation Checklist

### Phase 8: SSE Streaming (Required)

- [ ] **8.1 Core Implementation**
  - [ ] Create `/process-batch-stream` endpoint
  - [ ] Implement async event generator
  - [ ] Add SSE response headers
  - [ ] Implement progress events
  - [ ] Implement result events
  - [ ] Implement error events
  - [ ] Implement completion event
  - [ ] Add logging

- [ ] **8.2 Event Schemas**
  - [ ] Create Pydantic models for events
  - [ ] Add JSON serialization helpers
  - [ ] Validate event data

- [ ] **8.3 Testing**
  - [ ] Create `tests/test_streaming.py`
  - [ ] Test SSE connection and headers
  - [ ] Test all event types
  - [ ] Test error handling
  - [ ] Test with multiple files
  - [ ] Integration tests

- [ ] **8.4 Documentation**
  - [ ] Create `docs/STREAMING_GUIDE.md`
  - [ ] Add JavaScript examples
  - [ ] Add React component example
  - [ ] Update `API_REFERENCE.md`
  - [ ] Add cURL testing examples

### Phase 9: Parallel Processing (Optional)

- [ ] **9.1 Core Implementation**
  - [ ] Add `MAX_WORKERS` config setting
  - [ ] Extract single image processing function
  - [ ] Implement ThreadPoolExecutor
  - [ ] Test thread safety
  - [ ] Add worker error handling

- [ ] **9.2 Streaming + Parallel**
  - [ ] Create `/process-batch-fast` endpoint
  - [ ] Implement batched parallel execution
  - [ ] Stream results from parallel workers
  - [ ] Update progress calculations

- [ ] **9.3 Testing & Benchmarking**
  - [ ] Create benchmark script
  - [ ] Test with 2, 3, 4 workers
  - [ ] Test GPU mode stability
  - [ ] Document optimal configurations
  - [ ] Add performance tests

---

## Success Metrics

### Phase 8 Success Criteria
✅ Frontend receives first result immediately (not after all complete)  
✅ Progress bar shows real-time updates  
✅ Errors don't break the stream  
✅ All events properly formatted and parseable  
✅ Tests pass for all event types  
✅ Documentation complete with examples  

### Phase 9 Success Criteria (if implemented)
✅ 40-60% reduction in total processing time  
✅ Configurable worker count (2-4)  
✅ No race conditions or crashes  
✅ Safe for CPU mode, tested for GPU mode  
✅ Performance benchmarks documented  

---

## Timeline

| Phase | Task | Estimated Time | Priority |
|-------|------|---------------|----------|
| 8.1 | Core SSE endpoint | 1.5 hours | HIGH |
| 8.2 | Event schemas | 0.5 hours | HIGH |
| 8.3 | Testing | 1 hour | HIGH |
| 8.4 | Documentation | 1 hour | MEDIUM |
| **Phase 8 Total** | | **3-4 hours** | **REQUIRED** |
| 9.1 | Parallel core | 1.5 hours | LOW |
| 9.2 | Streaming + Parallel | 1 hour | LOW |
| 9.3 | Testing | 0.5 hours | LOW |
| **Phase 9 Total** | | **2-3 hours** | **OPTIONAL** |

---

## Deployment Strategy

1. **Deploy Phase 8 First** (Streaming)
   - Immediate UX improvement
   - No risk to existing functionality
   - Backward compatible (`/process-batch` still available)
   - Can deploy independently

2. **Deploy Phase 9 Later** (Parallel) - If needed
   - Test thoroughly in staging first
   - Start with `MAX_WORKERS=2`
   - Monitor CPU/GPU usage
   - Disable if any stability issues

3. **Rollout Plan**
   - Week 1: Deploy Phase 8 to staging, test with frontend
   - Week 2: Deploy Phase 8 to production
   - Week 3+: Evaluate need for Phase 9 based on user feedback

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| SSE connection drops | MEDIUM | Built-in reconnection, fallback to `/process-batch` |
| Browser compatibility | LOW | SSE supported in all modern browsers |
| Parallel processing crashes | HIGH | Phase 9 optional, can skip if problematic |
| GPU OOM with parallel | HIGH | Disable parallel for GPU mode, or max 2 workers |
| Thread safety issues | MEDIUM | Test thoroughly, add locks if needed |

---

## Next Steps

1. ✅ **Planning Complete** - This document
2. **Begin Implementation** - Start with Phase 8.1 (SSE endpoint)
3. **Test as You Go** - TDD approach, write tests first
4. **Document Frontend Integration** - Clear examples for frontend team
5. **Deploy Phase 8** - Get immediate UX wins
6. **Evaluate Phase 9** - Based on user feedback and performance needs

---

**Questions or Concerns?**
- Is SSE the right choice for your use case? (Answer: Yes, perfect fit)
- Should we implement Phase 9? (Answer: Phase 8 first, then evaluate)
- Timeline too aggressive? (Answer: Phase 8 is 3-4 hours, achievable)

**Ready to start implementation?** Let's begin with Phase 8.1! 🚀




