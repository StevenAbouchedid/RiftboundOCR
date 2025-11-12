# RiftboundOCR API Reference

**Quick reference for frontend developers integrating with the RiftboundOCR service.**

---

## Base URL

```
http://localhost:8080/api
```

When deployed, replace with your production URL.

---

## Endpoints

### 1. Health Check

**GET `/health`**

Check if the service is running and ready to process images.

**Response:**
```json
{
  "status": "healthy",
  "service": "RiftboundOCR",
  "version": "1.0.0",
  "matcher_loaded": true,
  "total_cards_in_db": 399
}
```

**Status Codes:**
- `200` - Service is healthy
- `503` - Service is unhealthy (OCR components not initialized)

---

### 2. Service Statistics

**GET `/stats`**

Get information about OCR capabilities and card database.

**Response:**
```json
{
  "matcher": {
    "total_cards": 399,
    "base_names": 350,
    "supported_languages": ["zh-CN", "en"]
  },
  "parser": {
    "ocr_engines": ["PaddleOCR", "EasyOCR"],
    "supported_formats": ["JPG", "PNG"],
    "max_file_size_mb": 10,
    "use_gpu": false
  }
}
```

---

### 3. Process Single Image ⭐

**POST `/process`**

Upload a Chinese decklist image and get back parsed cards with English translations.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body Parameters:**
  - `file` (required): Image file (JPG/PNG, max 10MB)

**Example (JavaScript/Fetch):**
```javascript
const formData = new FormData();
formData.append('file', imageFile);

const response = await fetch('http://localhost:8080/api/process', {
  method: 'POST',
  body: formData
});

const decklist = await response.json();
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8080/api/process \
  -F "file=@decklist.jpg"
```

**Response:**
```json
{
  "decklist_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "placement": 92,
    "event": "第一赛季区域公开赛-杭州赛区",
    "date": "2025-11-01"
  },
  "legend": [
    {
      "name_cn": "易, 锋芒毕现",
      "name_en": "Master Yi, The Wuju Bladesman",
      "quantity": 1,
      "card_number": "01IO060",
      "type_en": "Legend",
      "domain_en": "Ionia",
      "cost": "0",
      "rarity_en": "Champion",
      "image_url_en": "https://...",
      "match_score": 100.0,
      "match_type": "exact_full"
    }
  ],
  "main_deck": [
    {
      "name_cn": "背水一战",
      "name_en": "Blade's Edge",
      "quantity": 3,
      "card_number": "01NX043",
      "type_en": "Spell",
      "domain_en": "Noxus",
      "cost": "1",
      "rarity_en": "Common",
      "match_score": 95.5,
      "match_type": "fuzzy"
    }
  ],
  "battlefields": [
    {
      "name_cn": "艾欧尼亚战场",
      "name_en": "Ionian Battlefield",
      "quantity": 3,
      "card_number": "01IO001B",
      "type_en": "Battlefield",
      "match_score": 100.0
    }
  ],
  "runes": [
    {
      "name_cn": "主宰系",
      "name_en": "Domination Rune",
      "quantity": 3,
      "card_number": "01RU001",
      "type_en": "Rune",
      "match_score": 100.0
    }
  ],
  "side_deck": [],
  "stats": {
    "total_cards": 63,
    "matched_cards": 59,
    "accuracy": 93.65
  }
}
```

**Card Sections:**
- `legend`: 1 legendary card
- `main_deck`: 40 main deck cards
- `battlefields`: 3 battlefield cards
- `runes`: 12 rune cards
- `side_deck`: 0-8 sideboard cards

**Status Codes:**
- `200` - Successfully processed
- `400` - Invalid file type or size
- `500` - Processing error
- `503` - Service not ready

---

### 4. Process Batch

**POST `/process-batch`**

Upload multiple decklist images at once (max 10 per request).

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body Parameters:**
  - `files` (required): Array of image files

**Example (JavaScript/Fetch):**
```javascript
const formData = new FormData();
imageFiles.forEach(file => {
  formData.append('files', file);
});

const response = await fetch('http://localhost:8080/api/process-batch', {
  method: 'POST',
  body: formData
});

const batch = await response.json();
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8080/api/process-batch \
  -F "files=@deck1.jpg" \
  -F "files=@deck2.jpg" \
  -F "files=@deck3.jpg"
```

**Response:**
```json
{
  "total": 5,
  "successful": 4,
  "failed": 1,
  "average_accuracy": 92.5,
  "results": [
    {
      "decklist_id": "...",
      "metadata": {...},
      "legend": [...],
      "main_deck": [...],
      "stats": {...}
    }
  ]
}
```

**Limits:**
- Maximum 10 images per batch
- Each image max 10MB

**Status Codes:**
- `200` - Batch processed (check individual results for failures)
- `400` - Too many files or invalid request
- `503` - Service not ready

---

### 4a. Process Batch with Streaming ⭐ NEW

**POST `/process-batch-stream`**

Upload multiple decklist images with real-time progress updates and progressive results (Server-Sent Events).

**Why Use This?**
- ✅ See results immediately as each image completes (no waiting for entire batch)
- ✅ Real-time progress bar
- ✅ Start working on completed decklists while others process
- ✅ Better UX for 5-10 minute processing times

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body Parameters:**
  - `files` (required): Array of image files (max 10)

**Response:** Server-Sent Events (SSE) stream with 4 event types:

#### Event Types:

**1. `progress` Event** - Real-time status updates

```json
{
  "current": 3,
  "total": 10,
  "filename": "deck3.jpg",
  "status": "processing"
}
```

**2. `result` Event** - Completed decklist (as each finishes)

```json
{
  "index": 2,
  "filename": "deck3.jpg",
  "decklist": {
    "decklist_id": "...",
    "metadata": {...},
    "legend": [...],
    "main_deck": [...],
    "stats": {...}
  }
}
```

**3. `error` Event** - Individual failures (doesn't break stream)

```json
{
  "index": 5,
  "filename": "deck6.jpg",
  "error": "File size exceeds maximum",
  "error_type": "validation"
}
```

**4. `complete` Event** - Final statistics

```json
{
  "total": 10,
  "successful": 8,
  "failed": 2,
  "average_accuracy": 93.2,
  "processing_time_seconds": 245.5
}
```

**Example (JavaScript/Fetch):**

```javascript
const formData = new FormData();
imageFiles.forEach(file => formData.append('files', file));

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
    
    // Handle each event type
    switch (eventType) {
      case 'progress':
        updateProgressBar(eventData.current, eventData.total);
        break;
      case 'result':
        displayDecklist(eventData.decklist);  // Show immediately!
        break;
      case 'error':
        showError(eventData);
        break;
      case 'complete':
        showSummary(eventData);
        break;
    }
  }
}
```

**Example (cURL):**

```bash
curl -X POST http://localhost:8080/api/process-batch-stream \
  -F "files=@deck1.jpg" \
  -F "files=@deck2.jpg" \
  -N --no-buffer
```

**Status Codes:**
- `200` - Streaming started (events will follow)
- `400` - Too many files or invalid request
- `503` - Service not ready

**📚 Complete Guide:** See [STREAMING_GUIDE.md](./docs/STREAMING_GUIDE.md) for detailed frontend integration examples (React, Vue, vanilla JS).

---

### 4b. Process Batch with Parallel + Streaming 🚀 NEW

**POST `/process-batch-fast`**

Upload multiple images with **parallel processing** + streaming for maximum speed (40-60% faster than sequential).

**Why Use This?**
- 🚀 **40-60% faster** than sequential processing
- ⚡ Process 2-4 images **simultaneously**
- 📊 Still get real-time progress updates (SSE)
- 🎯 Best for high-volume batch processing

**Requirements:**
- Environment variable: `ENABLE_PARALLEL=true`
- Configure worker count: `MAX_WORKERS=2` (default: 2)

**Request:**
- Same as `/process-batch-stream`
- **Content-Type:** `multipart/form-data`
- **Body Parameters:**
  - `files` (required): Array of image files (max 10)

**Response:**
- Same SSE event stream as `/process-batch-stream`
- Events: `progress`, `result`, `error`, `complete`

**Performance:**
```
Sequential (10 images): 7.5 minutes
Parallel (2 workers):   3.75 minutes  (50% faster!)
Parallel (4 workers):   ~2 minutes    (70% faster!)
```

**Example (JavaScript):**
```javascript
// Same code as /process-batch-stream!
const response = await fetch('http://localhost:8080/api/process-batch-fast', {
  method: 'POST',
  body: formData
});

// ... handle SSE events same as streaming endpoint
```

**Configuration:**
```bash
# Enable parallel processing
export ENABLE_PARALLEL=true

# Set worker count (2-4 recommended for CPU, 1-2 for GPU)
export MAX_WORKERS=2
```

**Status Codes:**
- `200` - Streaming started
- `400` - Parallel processing not enabled or too many files
- `503` - Service not ready

**Note:** If parallel processing is not enabled, you'll get an error. Use `/process-batch-stream` instead.

---

### 5. Process and Save to Main API

**POST `/process-and-save`**

Process a decklist image and automatically save it to the main Riftbound API (if configured).

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body Parameters:**
  - `file` (required): Image file
  - `owner` (optional): Deck owner/player name (default: "Unknown")
  - `format_id` (optional): Format ID from main API (default: 1)

**Example (JavaScript/Fetch):**
```javascript
const formData = new FormData();
formData.append('file', imageFile);
formData.append('owner', 'Player Name');
formData.append('format_id', '1');

const response = await fetch('http://localhost:8080/api/process-and-save', {
  method: 'POST',
  body: formData
});

const savedDeck = await response.json();
```

**Response:**
```json
{
  "id": 123,
  "name": "Master Yi Aggro",
  "owner": "Player Name",
  "format_id": 1,
  "cards": [...],
  "ocr_stats": {
    "total_cards": 63,
    "matched_cards": 59,
    "accuracy": 93.65
  }
}
```

**Status Codes:**
- `200` - Successfully processed and saved
- `400` - Invalid file or no cards could be resolved
- `503` - Service or main API not available

---

## Data Structures

### CardData

Each card in the response contains:

| Field | Type | Description |
|-------|------|-------------|
| `name_cn` | string | Chinese card name (from OCR) |
| `name_en` | string | English card name (matched) |
| `quantity` | int | Card quantity (1-12) |
| `card_number` | string | Card number (e.g., "01IO060") |
| `type_en` | string | Card type (Legend, Unit, Spell, Battlefield, Rune) |
| `domain_en` | string | Card domain/region (Ionia, Noxus, etc.) |
| `cost` | string | Mana/energy cost |
| `rarity_en` | string | Rarity (Common, Rare, Epic, Champion) |
| `image_url_en` | string | Card image URL |
| `match_score` | float | Match confidence (0-100) |
| `match_type` | string | Match strategy used (exact_full, fuzzy, etc.) |

### DecklistMetadata

Tournament/event information:

| Field | Type | Description |
|-------|------|-------------|
| `placement` | int | Tournament placement/rank |
| `event` | string | Event name |
| `date` | string | Event date (YYYY-MM-DD) |

### DecklistStats

OCR accuracy statistics:

| Field | Type | Description |
|-------|------|-------------|
| `total_cards` | int | Total cards extracted |
| `matched_cards` | int | Successfully matched cards |
| `accuracy` | float | Match accuracy percentage (0-100) |

---

## Error Handling

All endpoints return standard HTTP error responses:

**400 Bad Request:**
```json
{
  "detail": "File must be an image (JPG/PNG)"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Processing failed: [error details]"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "OCR service not initialized"
}
```

---

## Constraints & Limits

- **Max file size:** 10MB per image
- **Max batch size:** 10 images per request
- **Supported formats:** JPG, PNG
- **Supported languages:** Chinese (input) → English (output)
- **Card deck sizes:** 
  - Legend: 1 card
  - Main Deck: 40 cards
  - Battlefields: 3 cards
  - Runes: 12 cards
  - Side Deck: 0-8 cards

---

## Integration Tips

### 1. Check Service Health First

Always verify the service is ready before processing images:

```javascript
async function isServiceReady() {
  const response = await fetch('http://localhost:8080/api/health');
  const health = await response.json();
  return health.status === 'healthy';
}
```

### 2. Display Match Scores

Show users the confidence of card matches:

```javascript
function getMatchQuality(score) {
  if (score >= 95) return 'Excellent';
  if (score >= 85) return 'Good';
  if (score >= 70) return 'Fair';
  return 'Poor - Verify Manually';
}
```

### 3. Handle Batch Processing

Process multiple images with progress tracking:

```javascript
async function processBatch(files) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  const response = await fetch('http://localhost:8080/api/process-batch', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  console.log(`${result.successful}/${result.total} successful`);
  console.log(`Average accuracy: ${result.average_accuracy}%`);
  
  return result.results;
}
```

### 4. Validate Before Upload

```javascript
function validateImage(file) {
  const validTypes = ['image/jpeg', 'image/png'];
  const maxSize = 10 * 1024 * 1024; // 10MB
  
  if (!validTypes.includes(file.type)) {
    throw new Error('Only JPG and PNG files are supported');
  }
  
  if (file.size > maxSize) {
    throw new Error('File size must be under 10MB');
  }
  
  return true;
}
```

---

## Support

For issues or questions:
- Check the main [README.md](./README.md)
- Review [QUICK_START.md](./QUICK_START.md) for setup instructions
- See test examples in `tests/` directory



