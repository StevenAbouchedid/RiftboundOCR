# RiftboundOCR - Complete API Reference & Hosting Guide

**Version:** 1.0.0  
**Last Updated:** November 2025  
**Service Type:** Microservice (FastAPI + Python)  
**Purpose:** Chinese Decklist OCR & Card Matching

---

## 📑 Table of Contents

1. [Service Architecture](#service-architecture)
2. [Base URL & Endpoints](#base-url--endpoints)
3. [API Routes Reference](#api-routes-reference)
4. [Request/Response Schemas](#requestresponse-schemas)
5. [Error Handling](#error-handling)
6. [Authentication](#authentication)
7. [Rate Limiting](#rate-limiting)
8. [Hosting & Deployment](#hosting--deployment)
9. [Environment Configuration](#environment-configuration)
10. [Performance & Scaling](#performance--scaling)

---

## Service Architecture

### Overview

RiftboundOCR is a **standalone microservice** designed to process Chinese decklist screenshots using OCR (Optical Character Recognition) and match them to English card data.

```
┌─────────────────────────────────────────────────────────────┐
│                        Architecture                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend (Next.js/React)                                   │
│       │                                                      │
│       ├─► POST /api/v1/process          (Single image)      │
│       ├─► POST /api/v1/process-batch    (Multiple images)   │
│       └─► POST /api/v1/process-batch-stream (SSE)          │
│                                                              │
│  RiftboundOCR Service (Python/FastAPI)                      │
│       │                                                      │
│       ├─► PaddleOCR (Chinese text)                          │
│       ├─► EasyOCR (Quantities)                              │
│       ├─► Tesseract (Numeric fallback)                      │
│       └─► Card Matcher (RapidFuzz)                          │
│                                                              │
│  Optional: Main Riftbound API                               │
│       └─► Deck storage & management                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.115.4 | REST API & async handling |
| **Server** | Uvicorn 0.32.0 | ASGI web server |
| **OCR Engines** | PaddleOCR 2.9.1 | Chinese text recognition |
|  | EasyOCR 1.7.2 | Quantity detection |
|  | Tesseract 5.x | Numeric field fallback |
| **Image Processing** | OpenCV 4.10, Pillow 10.4 | Image manipulation |
| **Matching** | RapidFuzz 3.10.1 | Fuzzy string matching |
| **ML Framework** | PyTorch (CPU/GPU) | Neural networks |
| **Containerization** | Docker | Deployment packaging |
| **Hosting** | Railway.app | Production hosting |

### System Requirements

| Resource | Minimum | Recommended | Notes |
|----------|---------|-------------|-------|
| **CPU** | 2 cores | 4+ cores | CPU mode works fine |
| **RAM** | 2 GB | 4-8 GB | Models take ~1.5GB |
| **Disk** | 5 GB | 10+ GB | Models + temp files |
| **Network** | 10 Mbps | 100+ Mbps | Image uploads |
| **Python** | 3.11+ | 3.12 | NOT 3.13 (compatibility) |

---

## Base URL & Endpoints

### Development
```
http://localhost:8002
```

### Production (Railway)
```
https://riftbound-ocr.up.railway.app
```

### API Versioning
```
/api/v1/*
```

All routes are prefixed with `/api/v1/` for version control.

---

## API Routes Reference

### 1. Health Check

**Endpoint:** `GET /api/v1/health`

**Purpose:** Check service status and availability

**Authentication:** None

**Rate Limit:** Unlimited

#### Request
```http
GET /api/v1/health HTTP/1.1
Host: localhost:8002
Accept: application/json
```

#### Response (200 OK)
```json
{
  "status": "healthy",
  "service": "RiftboundOCR",
  "version": "1.0.0",
  "matcher_loaded": true,
  "total_cards_in_db": 322
}
```

#### Response (503 Service Unavailable)
```json
{
  "status": "unhealthy",
  "service": "RiftboundOCR",
  "version": "1.0.0",
  "matcher_loaded": false,
  "total_cards_in_db": 0,
  "error": "Card matcher not initialized"
}
```

#### Response Schema
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "healthy" or "unhealthy" |
| `service` | string | Service name |
| `version` | string | API version |
| `matcher_loaded` | boolean | Card matcher initialization status |
| `total_cards_in_db` | number | Number of cards in database |
| `error` | string? | Error message if unhealthy |

#### Use Cases
- ✅ Load balancer health checks
- ✅ Monitoring/alerting systems
- ✅ Pre-flight validation before uploads
- ✅ Debugging service issues

---

### 2. Service Statistics

**Endpoint:** `GET /api/v1/stats`

**Purpose:** Get detailed service statistics and capabilities

**Authentication:** None

**Rate Limit:** Unlimited

#### Request
```http
GET /api/v1/stats HTTP/1.1
Host: localhost:8002
Accept: application/json
```

#### Response (200 OK)
```json
{
  "matcher": {
    "total_cards": 322,
    "card_types": ["Legend", "Unit", "Spell", "Artifact", "Battlefield"],
    "domains": ["Ionia", "Noxus", "Demacia", "Shadow Isles", "Freljord", "Piltover & Zaun"],
    "matching_strategies": [
      "exact_full",
      "exact_base",
      "comma_insertion_base",
      "fuzzy_base",
      "fuzzy_full"
    ]
  },
  "parser": {
    "supported_formats": ["JPG", "PNG", "JPEG"],
    "max_file_size_mb": 10,
    "use_gpu": false
  }
}
```

#### Response Schema
| Field | Type | Description |
|-------|------|-------------|
| `matcher.total_cards` | number | Total cards in database |
| `matcher.card_types` | string[] | Available card types |
| `matcher.domains` | string[] | Available domains/regions |
| `matcher.matching_strategies` | string[] | Matching algorithm names |
| `parser.supported_formats` | string[] | Accepted image formats |
| `parser.max_file_size_mb` | number | Maximum upload size |
| `parser.use_gpu` | boolean | GPU acceleration status |

#### Use Cases
- ✅ Frontend capability discovery
- ✅ Admin dashboards
- ✅ Integration testing
- ✅ Documentation generation

---

### 3. Process Single Image

**Endpoint:** `POST /api/v1/process`

**Purpose:** Upload and process a single decklist image

**Authentication:** None (add if needed)

**Rate Limit:** 60 requests/minute per IP

**Processing Time:** 30-60 seconds

#### Request
```http
POST /api/v1/process HTTP/1.1
Host: localhost:8002
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="decklist.jpg"
Content-Type: image/jpeg

[Binary image data]
------WebKitFormBoundary--
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8002/api/v1/process" \
  -H "accept: application/json" \
  -F "file=@decklist.jpg"
```

**JavaScript Example:**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8002/api/v1/process', {
  method: 'POST',
  body: formData
});

const decklist = await response.json();
```

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Image file (JPG/PNG) |

#### Validation Rules
- ✅ File must be image/* MIME type
- ✅ Max file size: 10 MB
- ✅ Supported formats: JPG, PNG, JPEG
- ✅ Recommended resolution: 1080p+

#### Response (200 OK)
```json
{
  "decklist_id": "abc123-def456-ghi789",
  "metadata": {
    "player": "Ai.闪闪",
    "deck_name": "卡莎",
    "placement": 1,
    "event": "第一赛季区域公开赛-北京赛区",
    "date": "2025-08-30",
    "legend_name_en": "Kai'Sa, Daughter of the Void"
  },
  "legend": [
    {
      "name_cn": "卡莎, 虚空之女",
      "name_en": "Kai'Sa, Daughter of the Void",
      "quantity": 1,
      "card_number": "01PZ048",
      "type_en": "Legend",
      "domain_en": "Piltover & Zaun",
      "cost": "0",
      "rarity_en": "Champion",
      "image_url_en": "https://example.com/card.jpg",
      "match_score": 100,
      "match_type": "exact_full"
    }
  ],
  "main_deck": [
    {
      "name_cn": "沃利贝尔",
      "name_en": "Volibear",
      "quantity": 2,
      "card_number": "05FR005",
      "type_en": "Unit",
      "domain_en": "Freljord",
      "cost": "7",
      "rarity_en": "Champion",
      "match_score": 95,
      "match_type": "exact_base"
    }
    // ... more cards
  ],
  "battlefields": [
    {
      "name_cn": "力量方尖碑",
      "name_en": "Obelisk of Power",
      "quantity": 1,
      "card_number": "06NX026",
      "type_en": "Battlefield",
      "domain_en": "Noxus",
      "match_score": 100,
      "match_type": "exact_full"
    }
    // ... 3 total
  ],
  "runes": [
    {
      "name_cn": "翠意符文",
      "name_en": "Rune of Verdant Growth",
      "quantity": 6,
      "card_number": "RUNE_001",
      "type_en": "Rune",
      "match_score": 100,
      "match_type": "exact_full"
    }
    // ... 12 total
  ],
  "side_deck": [
    {
      "name_cn": "坚毅不倒",
      "name_en": "Unyielding Spirit",
      "quantity": 2,
      "card_number": "02DE041",
      "type_en": "Spell",
      "domain_en": "Demacia",
      "match_score": 98,
      "match_type": "fuzzy_base"
    }
    // ... 0-8 cards
  ],
  "unmatched": [
    {
      "name_cn": "未知卡牌",
      "name_en": null,
      "quantity": 1,
      "card_number": null,
      "match_score": 0,
      "match_type": "no_match"
    }
  ],
  "stats": {
    "total_cards": 63,
    "matched_cards": 59,
    "accuracy": 93.65
  }
}
```

#### Response Schema (Detailed)

**Root Object:**
| Field | Type | Description |
|-------|------|-------------|
| `decklist_id` | string | Unique UUID for this decklist |
| `metadata` | object | Tournament/player information |
| `legend` | array | Legend cards (1 expected) |
| `main_deck` | array | Main deck cards (40 expected) |
| `battlefields` | array | Battlefield cards (3 expected) |
| `runes` | array | Rune cards (12 expected) |
| `side_deck` | array | Side deck cards (0-8) |
| `unmatched` | array | Cards that couldn't be matched |
| `stats` | object | Accuracy statistics |

**Metadata Object:**
| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `player` | string | Yes | Player name |
| `deck_name` | string | Yes | Deck/Legend name (Chinese) |
| `placement` | number | Yes | Tournament placement rank |
| `event` | string | Yes | Event/tournament name |
| `date` | string | Yes | Event date (YYYY-MM-DD) |
| `legend_name_en` | string | Yes | English legend name |

**Card Object:**
| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `name_cn` | string | No | Chinese card name |
| `name_en` | string | Yes | English card name |
| `quantity` | number | No | Number of copies (1-12) |
| `card_number` | string | Yes | Card set/number (e.g., "01PZ048") |
| `type_en` | string | Yes | Card type (Legend, Unit, Spell, etc.) |
| `domain_en` | string | Yes | Card domain/region |
| `cost` | string | Yes | Mana/energy cost |
| `rarity_en` | string | Yes | Card rarity |
| `image_url_en` | string | Yes | Card image URL |
| `match_score` | number | Yes | Confidence score (0-100) |
| `match_type` | string | Yes | Matching strategy used |

**Stats Object:**
| Field | Type | Description |
|-------|------|-------------|
| `total_cards` | number | Total individual cards detected |
| `matched_cards` | number | Successfully matched cards |
| `accuracy` | number | Match accuracy percentage |

#### Error Responses

**400 Bad Request - Invalid file type:**
```json
{
  "detail": "File must be an image (JPG/PNG)"
}
```

**400 Bad Request - File too large:**
```json
{
  "detail": "File size (12.3MB) exceeds maximum (10MB)"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Processing failed: OCR engine error"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "Card matcher not initialized"
}
```

#### Use Cases
- ✅ Main decklist upload workflow
- ✅ Mobile app integration
- ✅ Desktop application integration
- ✅ Manual deck entry

---

### 4. Process Batch (Non-Streaming)

**Endpoint:** `POST /api/v1/process-batch`

**Purpose:** Upload and process multiple images at once (sequential)

**Authentication:** None

**Rate Limit:** 10 requests/minute per IP

**Processing Time:** 30-60s × number of images

#### Request
```http
POST /api/v1/process-batch HTTP/1.1
Host: localhost:8002
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="files"; filename="deck1.jpg"
Content-Type: image/jpeg

[Binary image data]
------WebKitFormBoundary
Content-Disposition: form-data; name="files"; filename="deck2.jpg"
Content-Type: image/jpeg

[Binary image data]
------WebKitFormBoundary--
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8002/api/v1/process-batch" \
  -F "files=@deck1.jpg" \
  -F "files=@deck2.jpg" \
  -F "files=@deck3.jpg"
```

**JavaScript Example:**
```javascript
const formData = new FormData();
for (const file of fileInput.files) {
  formData.append('files', file);
}

const response = await fetch('http://localhost:8002/api/v1/process-batch', {
  method: 'POST',
  body: formData
});

const batch = await response.json();
```

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `files` | File[] | Yes | Array of image files |

#### Validation Rules
- ✅ Each file must be image/* MIME type
- ✅ Max file size per image: 10 MB
- ✅ Max batch size: 20 images
- ✅ Total batch size: 100 MB

#### Response (200 OK)
```json
{
  "batch_id": "batch-xyz789",
  "total_processed": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "filename": "deck1.jpg",
      "status": "success",
      "decklist": {
        "decklist_id": "abc123",
        "metadata": { /* ... */ },
        "legend": [ /* ... */ ],
        "main_deck": [ /* ... */ ],
        "stats": { /* ... */ }
      }
    },
    {
      "filename": "deck2.jpg",
      "status": "success",
      "decklist": { /* ... */ }
    },
    {
      "filename": "deck3.jpg",
      "status": "error",
      "error": "Processing failed: OCR timeout"
    }
  ],
  "processing_time_seconds": 135.4,
  "average_accuracy": 92.5
}
```

#### Response Schema
| Field | Type | Description |
|-------|------|-------------|
| `batch_id` | string | Unique batch identifier |
| `total_processed` | number | Total images attempted |
| `successful` | number | Successfully processed |
| `failed` | number | Failed to process |
| `results` | array | Individual results per image |
| `processing_time_seconds` | number | Total processing time |
| `average_accuracy` | number | Average match accuracy |

**Result Item:**
| Field | Type | Description |
|-------|------|-------------|
| `filename` | string | Original filename |
| `status` | string | "success" or "error" |
| `decklist` | object? | Full decklist (if success) |
| `error` | string? | Error message (if error) |

#### Use Cases
- ✅ Tournament result batch import
- ✅ Bulk deck digitization
- ✅ Archival projects

#### ⚠️ Limitations
- ❌ **Blocking:** Client must wait for all images to complete
- ❌ **No progress updates:** Cannot show real-time progress
- ⚠️ **Memory intensive:** All results held in memory
- ⚠️ **Timeout risk:** May timeout for large batches

**Recommendation:** Use `/process-batch-stream` for better UX

---

### 5. Process Batch (Streaming - SSE)

**Endpoint:** `POST /api/v1/process-batch-stream`

**Purpose:** Upload and process multiple images with real-time progress updates

**Authentication:** None

**Rate Limit:** 10 requests/minute per IP

**Protocol:** Server-Sent Events (SSE)

**Processing Time:** 30-60s × number of images (but progressive results)

#### Request
```http
POST /api/v1/process-batch-stream HTTP/1.1
Host: localhost:8002
Content-Type: multipart/form-data
Accept: text/event-stream

[Same multipart data as batch endpoint]
```

**JavaScript Example (EventSource):**
```javascript
// Note: EventSource doesn't support POST, so use fetch with streaming
const formData = new FormData();
for (const file of fileInput.files) {
  formData.append('files', file);
}

const response = await fetch('http://localhost:8002/api/v1/process-batch-stream', {
  method: 'POST',
  body: formData
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      handleEvent(data);
    }
  }
}
```

**React Hook Example:**
```typescript
function useStreamingUpload() {
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [results, setResults] = useState([]);
  
  const uploadFiles = async (files: File[]) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const response = await fetch('/api/v1/process-batch-stream', {
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
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (!line.trim() || line.startsWith(':')) continue;
        
        if (line.startsWith('event: ')) {
          const eventType = line.slice(7);
          continue;
        }
        
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          
          if (data.event === 'progress') {
            setProgress({ current: data.current, total: data.total });
          } else if (data.event === 'result') {
            setResults(prev => [...prev, data.decklist]);
          }
        }
      }
    }
  };
  
  return { progress, results, uploadFiles };
}
```

#### SSE Event Types

**1. Progress Event**
```
event: progress
data: {"event":"progress","current":2,"total":5,"filename":"deck2.jpg","status":"processing"}
```

**2. Result Event**
```
event: result
data: {"event":"result","index":1,"decklist":{...full decklist object...}}
```

**3. Error Event**
```
event: error
data: {"event":"error","index":3,"filename":"deck3.jpg","error":"OCR failed"}
```

**4. Complete Event**
```
event: complete
data: {"event":"complete","total":5,"successful":4,"failed":1,"average_accuracy":93.2}
```

#### Event Schemas

**Progress Event:**
| Field | Type | Description |
|-------|------|-------------|
| `event` | "progress" | Event type |
| `current` | number | Current image index (1-based) |
| `total` | number | Total images |
| `filename` | string | Current file being processed |
| `status` | string | "processing" |

**Result Event:**
| Field | Type | Description |
|-------|------|-------------|
| `event` | "result" | Event type |
| `index` | number | Image index (0-based) |
| `decklist` | object | Full decklist object |

**Error Event:**
| Field | Type | Description |
|-------|------|-------------|
| `event` | "error" | Event type |
| `index` | number | Image index (0-based) |
| `filename` | string | Failed filename |
| `error` | string | Error message |

**Complete Event:**
| Field | Type | Description |
|-------|------|-------------|
| `event` | "complete" | Event type |
| `total` | number | Total images processed |
| `successful` | number | Successfully processed |
| `failed` | number | Failed to process |
| `average_accuracy` | number | Average match accuracy |

#### Use Cases
- ✅ **Best UX:** Progressive results as they complete
- ✅ Tournament bulk import with progress bars
- ✅ Real-time feedback for users
- ✅ Start working on first results while others process

#### Advantages over `/process-batch`
- ✅ **Progressive results:** Show results immediately
- ✅ **Real-time progress:** Update UI in real-time
- ✅ **Better UX:** Users don't wait for entire batch
- ✅ **Memory efficient:** Stream results, don't buffer all
- ✅ **Resilient:** Errors don't block other images

---

### 6. Process Batch (Parallel - Fast)

**Endpoint:** `POST /api/v1/process-batch-fast`

**Purpose:** Process multiple images in parallel with streaming results

**Authentication:** None

**Rate Limit:** 5 requests/minute per IP

**Protocol:** Server-Sent Events (SSE)

**Processing Time:** 50-70% faster than sequential

**⚠️ Status:** EXPERIMENTAL - Disabled by default

#### Configuration
Set environment variable to enable:
```bash
ENABLE_PARALLEL_PROCESSING=true
MAX_WORKERS=2  # Recommended: 2-4
```

#### Request
Same as `/process-batch-stream`

#### Response
Same SSE events as `/process-batch-stream`, but results may arrive out of order

#### Performance Comparison
| Method | 10 Images | Notes |
|--------|-----------|-------|
| Sequential | ~7.5 min | Default |
| Parallel (2 workers) | ~3.75 min | 50% faster |
| Parallel (4 workers) | ~2 min | 70% faster |

#### Use Cases
- ✅ Large tournament imports (20+ images)
- ✅ When speed is critical
- ⚠️ CPU mode only (GPU may OOM)

#### Limitations
- ⚠️ **Out-of-order results:** Results may not arrive sequentially
- ⚠️ **Higher memory:** Multiple workers = more RAM
- ⚠️ **GPU risk:** May cause OOM on GPU
- ⚠️ **Experimental:** May change in future versions

---

### 7. Save to Main API (Optional)

**Endpoint:** `POST /api/v1/process-and-save`

**Purpose:** Process image and automatically save to main Riftbound API

**Authentication:** Requires main API key

**Rate Limit:** 30 requests/minute per API key

**Processing Time:** 30-60s + network time

#### Configuration
Set environment variables:
```bash
MAIN_API_URL=https://riftbound-api.vercel.app/api
MAIN_API_KEY=your_api_key_here
```

#### Request
Same as `/process` endpoint

#### Response (200 OK)
```json
{
  "ocr_result": {
    "decklist_id": "local-abc123",
    "metadata": { /* ... */ },
    "legend": [ /* ... */ ],
    "stats": { /* ... */ }
  },
  "main_api_result": {
    "deck_id": "remote-xyz789",
    "created_at": "2025-11-12T12:00:00Z",
    "url": "https://riftbound.gg/decks/xyz789"
  }
}
```

#### Use Cases
- ✅ Direct integration with main deck database
- ✅ Tournament organizers with API keys
- ✅ Automated deck archival

#### Error Handling
If main API fails, OCR result is still returned:
```json
{
  "ocr_result": { /* ... successful OCR ... */ },
  "main_api_result": {
    "error": "Failed to create deck: Network timeout",
    "deck_id": null
  }
}
```

---

## Request/Response Schemas

### Complete TypeScript Definitions

```typescript
// ============================================================================
// METADATA
// ============================================================================

export interface DecklistMetadata {
  /** Player name (e.g., "Ai.闪闪") */
  player: string | null;
  
  /** Deck/Legend name in Chinese (e.g., "卡莎") */
  deck_name: string | null;
  
  /** Tournament placement rank (e.g., 1, 2, 92) */
  placement: number | null;
  
  /** Event/tournament name */
  event: string | null;
  
  /** Event date in YYYY-MM-DD format */
  date: string | null;
  
  /** English legend name (e.g., "Kai'Sa, Daughter of the Void") */
  legend_name_en: string | null;
}

// ============================================================================
// CARDS
// ============================================================================

export interface CardData {
  /** Chinese card name (as OCR'd from image) */
  name_cn: string;
  
  /** English card name (from database) */
  name_en: string | null;
  
  /** Number of copies (1-12) */
  quantity: number;
  
  /** Card set and number (e.g., "01PZ048") */
  card_number: string | null;
  
  /** Card type (Legend, Unit, Spell, Artifact, Battlefield, Rune) */
  type_en: string | null;
  
  /** Card domain/region */
  domain_en: string | null;
  
  /** Mana/energy cost */
  cost: string | null;
  
  /** Card rarity (Common, Rare, Epic, Champion, etc.) */
  rarity_en: string | null;
  
  /** URL to card image */
  image_url_en: string | null;
  
  /** Match confidence score (0-100) */
  match_score: number | null;
  
  /** Matching strategy used */
  match_type: 'exact_full' | 'exact_base' | 'comma_insertion_base' | 'fuzzy_base' | 'fuzzy_full' | 'no_match' | null;
}

// ============================================================================
// STATS
// ============================================================================

export interface DecklistStats {
  /** Total individual cards detected */
  total_cards: number;
  
  /** Successfully matched cards */
  matched_cards: number;
  
  /** Match accuracy percentage (0-100) */
  accuracy: number;
}

// ============================================================================
// RESPONSES
// ============================================================================

export interface DecklistResponse {
  /** Unique decklist identifier (UUID) */
  decklist_id: string;
  
  /** Tournament and player metadata */
  metadata: DecklistMetadata;
  
  /** Legend cards (1 expected) */
  legend: CardData[];
  
  /** Main deck cards (40 expected) */
  main_deck: CardData[];
  
  /** Battlefield cards (3 expected) */
  battlefields: CardData[];
  
  /** Rune cards (12 expected) */
  runes: CardData[];
  
  /** Side deck cards (0-8 expected) */
  side_deck: CardData[];
  
  /** Unmatched cards */
  unmatched: CardData[];
  
  /** Accuracy statistics */
  stats: DecklistStats;
}

export interface BatchProcessResponse {
  batch_id: string;
  total_processed: number;
  successful: number;
  failed: number;
  results: BatchResult[];
  processing_time_seconds: number;
  average_accuracy: number;
}

export interface BatchResult {
  filename: string;
  status: 'success' | 'error';
  decklist?: DecklistResponse;
  error?: string;
}

// ============================================================================
// SSE EVENTS
// ============================================================================

export interface SSEProgressEvent {
  event: 'progress';
  current: number;
  total: number;
  filename: string;
  status: 'processing';
}

export interface SSEResultEvent {
  event: 'result';
  index: number;
  decklist: DecklistResponse;
}

export interface SSEErrorEvent {
  event: 'error';
  index: number;
  filename: string;
  error: string;
}

export interface SSECompleteEvent {
  event: 'complete';
  total: number;
  successful: number;
  failed: number;
  average_accuracy: number;
}

export type SSEEvent = SSEProgressEvent | SSEResultEvent | SSEErrorEvent | SSECompleteEvent;

// ============================================================================
// HEALTH & STATS
// ============================================================================

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  service: string;
  version: string;
  matcher_loaded: boolean;
  total_cards_in_db: number;
  error?: string;
}

export interface StatsResponse {
  matcher: {
    total_cards: number;
    card_types: string[];
    domains: string[];
    matching_strategies: string[];
  };
  parser: {
    supported_formats: string[];
    max_file_size_mb: number;
    use_gpu: boolean;
  };
}
```

---

## Error Handling

### Error Response Format

All errors follow this structure:
```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| **200** | Success | Request processed successfully |
| **400** | Bad Request | Invalid file, wrong format, file too large |
| **404** | Not Found | Invalid endpoint |
| **413** | Payload Too Large | File exceeds 10MB |
| **422** | Unprocessable Entity | Validation error (FastAPI) |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | OCR failure, matcher error |
| **503** | Service Unavailable | Service not initialized |

### Error Examples

**Invalid file type:**
```json
{
  "detail": "File must be an image (JPG/PNG)"
}
```

**File too large:**
```json
{
  "detail": "File size (12.3MB) exceeds maximum (10MB)"
}
```

**Processing failed:**
```json
{
  "detail": "Processing failed: OCR engine error"
}
```

**Service unavailable:**
```json
{
  "detail": "Card matcher not initialized"
}
```

### Error Handling Best Practices

```typescript
async function uploadDecklist(file: File) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/v1/process', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }
    
    return await response.json();
    
  } catch (error) {
    if (error instanceof TypeError) {
      // Network error
      console.error('Network error:', error);
      throw new Error('Unable to connect to OCR service');
    } else {
      // API error
      throw error;
    }
  }
}
```

---

## Authentication

### Current Status
**No authentication required** for public deployment

### Future Authentication Options

#### Option 1: API Key (Header)
```http
POST /api/v1/process HTTP/1.1
X-API-Key: your_api_key_here
```

#### Option 2: Bearer Token (JWT)
```http
POST /api/v1/process HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Option 3: Main API Integration
Use main Riftbound API authentication, pass through

### Implementation Guide

To add API key authentication:

1. **Update `src/config.py`:**
```python
class Settings(BaseSettings):
    api_key: str = Field(default="", env="API_KEY")
```

2. **Create middleware:**
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

3. **Add to routes:**
```python
@router.post("/process", dependencies=[Depends(verify_api_key)])
async def process_single_image(file: UploadFile = File(...)):
    # ...
```

---

## Rate Limiting

### Current Limits (Recommended)

| Endpoint | Limit | Window | Notes |
|----------|-------|--------|-------|
| `/health` | Unlimited | - | Health checks |
| `/stats` | Unlimited | - | Statistics |
| `/process` | 60 req | 1 minute | Per IP |
| `/process-batch` | 10 req | 1 minute | Per IP |
| `/process-batch-stream` | 10 req | 1 minute | Per IP |
| `/process-batch-fast` | 5 req | 1 minute | Per IP |

### Implementation

**Using SlowAPI (Python):**
```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/process")
@limiter.limit("60/minute")
async def process_single_image(request: Request, file: UploadFile = File(...)):
    # ...
```

**Using Nginx (Reverse Proxy):**
```nginx
http {
    limit_req_zone $binary_remote_addr zone=ocr:10m rate=60r/m;
    
    server {
        location /api/v1/process {
            limit_req zone=ocr burst=5 nodelay;
            proxy_pass http://ocr_backend;
        }
    }
}
```

---

## Hosting & Deployment

### Railway.app (Recommended)

#### Why Railway?
- ✅ **Easy deployment:** Git push to deploy
- ✅ **Docker support:** Native Dockerfile deployment
- ✅ **Persistent storage:** For model caching
- ✅ **Auto-scaling:** Based on traffic
- ✅ **Free tier:** $5 credit/month
- ✅ **Logs:** Built-in logging and monitoring

#### Deployment Steps

**1. Prepare Repository**
```bash
# Ensure these files exist:
- Dockerfile
- railway.toml
- requirements.txt
- src/
- resources/
```

**2. Create Railway Project**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to GitHub repo (or deploy directly)
railway link
```

**3. Configure Environment**

In Railway dashboard, set:
```
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8002
PYTHONUNBUFFERED=1
USE_GPU=false

# Optional:
MAIN_API_URL=https://your-main-api.vercel.app/api
MAIN_API_KEY=your_key_here
```

**4. Deploy**
```bash
railway up

# Or push to GitHub (if linked)
git push origin main
```

**5. Configure Domain**

Railway provides:
- ✅ Auto-generated URL: `https://your-service.up.railway.app`
- ✅ Custom domain support: `ocr.yourdomain.com`

#### Railway Configuration File

**`railway.toml`:**
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "python start_server.py"
healthcheckPath = "/api/v1/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[env]
SERVICE_HOST = "0.0.0.0"
SERVICE_PORT = "8002"
PYTHONUNBUFFERED = "1"
```

#### Estimated Costs

| Resource | Free Tier | Paid |
|----------|-----------|------|
| **RAM** | 512MB-8GB | $0.000231/GB/min |
| **CPU** | Shared | $0.000463/CPU/min |
| **Storage** | 1GB | $0.25/GB/month |
| **Network** | 100GB | $0.10/GB |

**Monthly estimate (moderate usage):**
- 2GB RAM, 1 CPU, 24/7 uptime: ~$20-30/month
- With scale-to-zero: ~$5-10/month

---

### Docker Deployment (Self-Hosted)

#### Build Image

```bash
docker build -t riftbound-ocr:latest .
```

#### Run Container

```bash
docker run -d \
  --name riftbound-ocr \
  -p 8002:8002 \
  -v ocr_models:/root/.paddleocr \
  -v ocr_easyocr:/root/.EasyOCR \
  -e SERVICE_HOST=0.0.0.0 \
  -e SERVICE_PORT=8002 \
  --restart unless-stopped \
  riftbound-ocr:latest
```

#### Docker Compose

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  ocr:
    build: .
    container_name: riftbound-ocr
    ports:
      - "8002:8002"
    volumes:
      - ocr_models:/root/.paddleocr
      - ocr_easyocr:/root/.EasyOCR
      - ./resources:/app/resources:ro
    environment:
      - SERVICE_HOST=0.0.0.0
      - SERVICE_PORT=8002
      - USE_GPU=false
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

volumes:
  ocr_models:
  ocr_easyocr:
```

**Run:**
```bash
docker-compose up -d
```

---

### VPS Deployment (DigitalOcean, AWS EC2, etc.)

#### Requirements
- **OS:** Ubuntu 20.04+ or Debian 11+
- **RAM:** 4GB minimum, 8GB recommended
- **CPU:** 2+ cores
- **Disk:** 20GB

#### Setup Script

```bash
#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install python3.12 python3.12-venv python3.12-dev -y

# Install system dependencies
sudo apt install -y \
  libgl1 \
  libglib2.0-0 \
  libsm6 \
  libxext6 \
  libxrender1 \
  libgomp1 \
  git \
  nginx

# Clone repository
git clone https://github.com/yourusername/RiftboundOCR.git
cd RiftboundOCR

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/riftbound-ocr.service > /dev/null <<EOF
[Unit]
Description=RiftboundOCR Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment="PATH=$PWD/venv/bin"
ExecStart=$PWD/venv/bin/python start_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable riftbound-ocr
sudo systemctl start riftbound-ocr

# Setup Nginx reverse proxy
sudo tee /etc/nginx/sites-available/riftbound-ocr > /dev/null <<'EOF'
server {
    listen 80;
    server_name ocr.yourdomain.com;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://localhost:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # SSE support
        proxy_buffering off;
        proxy_cache off;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/riftbound-ocr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d ocr.yourdomain.com

echo "Deployment complete!"
echo "Service running at: https://ocr.yourdomain.com"
```

---

### Vercel (NOT Recommended)

**❌ Why not Vercel:**
- Serverless functions limited to 10s execution (OCR takes 30-60s)
- 50MB function size limit (models are 2-3GB)
- No persistent storage for model caching

**✅ What to use Vercel for:**
- Main API (deck storage, user management)
- Frontend (Next.js, React)

---

## Environment Configuration

### Complete Environment Variables

```bash
# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================

# Service name
APP_NAME="RiftboundOCR"

# Service version
APP_VERSION="1.0.0"

# Host to bind to (0.0.0.0 for external access, 127.0.0.1 for local only)
SERVICE_HOST="0.0.0.0"

# Port to listen on
SERVICE_PORT="8002"

# =============================================================================
# OCR ENGINE CONFIGURATION
# =============================================================================

# Use GPU acceleration (requires CUDA)
USE_GPU="false"

# PaddleOCR detection threshold
DET_DB_THRESH="0.3"

# PaddleOCR box threshold
DET_DB_BOX_THRESH="0.6"

# =============================================================================
# FILE UPLOAD CONFIGURATION
# =============================================================================

# Maximum file size in MB
MAX_FILE_SIZE_MB="10"

# Supported image formats (comma-separated)
SUPPORTED_FORMATS="jpg,jpeg,png"

# =============================================================================
# CARD DATABASE
# =============================================================================

# Path to card mapping CSV
CARD_MAPPING_PATH="resources/card_mappings_final.csv"

# =============================================================================
# PARALLEL PROCESSING (OPTIONAL)
# =============================================================================

# Enable parallel processing (EXPERIMENTAL)
ENABLE_PARALLEL_PROCESSING="false"

# Maximum worker threads (2-4 recommended)
MAX_WORKERS="2"

# =============================================================================
# MAIN API INTEGRATION (OPTIONAL)
# =============================================================================

# Main Riftbound API URL
MAIN_API_URL=""

# Main API authentication key
MAIN_API_KEY=""

# Timeout for main API requests (seconds)
MAIN_API_TIMEOUT="30"

# =============================================================================
# LOGGING
# =============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL="INFO"

# Log format (simple, detailed)
LOG_FORMAT="detailed"

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

# Allowed origins (comma-separated, * for all)
CORS_ORIGINS="*"

# Allow credentials
CORS_ALLOW_CREDENTIALS="true"

# Allowed methods
CORS_ALLOW_METHODS="GET,POST,OPTIONS"

# =============================================================================
# PYTHON CONFIGURATION
# =============================================================================

# Unbuffered Python output (for Docker logs)
PYTHONUNBUFFERED="1"

# Don't write .pyc files
PYTHONDONTWRITEBYTECODE="1"
```

### `.env.example` File

Create this in your repository:
```bash
# Copy this to .env and customize

# Service
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8002
USE_GPU=false

# File uploads
MAX_FILE_SIZE_MB=10

# Card database
CARD_MAPPING_PATH=resources/card_mappings_final.csv

# Optional: Main API integration
# MAIN_API_URL=https://your-api.vercel.app/api
# MAIN_API_KEY=your_key_here

# Logging
LOG_LEVEL=INFO

# Python
PYTHONUNBUFFERED=1
```

---

## Performance & Scaling

### Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Processing Time** | 30-60s | Per image (CPU mode) |
| **GPU Speedup** | 2-3x faster | Requires CUDA GPU |
| **Accuracy** | 93-96% | Card matching accuracy |
| **Metadata Accuracy** | 96% | Tournament metadata |
| **Throughput** | 60-120 img/hr | Single worker |
| **Memory Usage** | 1.5-2GB | Models + processing |
| **Cold Start** | 10-15s | Model loading time |

### Optimization Tips

#### 1. Model Caching
```dockerfile
# In Dockerfile
VOLUME ["/root/.paddleocr", "/root/.EasyOCR"]

# Or docker run
docker run -v ocr_models:/root/.paddleocr ...
```

#### 2. Enable GPU (if available)
```bash
USE_GPU=true

# Requires CUDA-enabled Docker
docker run --gpus all ...
```

#### 3. Horizontal Scaling
```yaml
# Docker Compose with multiple workers
services:
  ocr1:
    build: .
    ports: ["8002:8002"]
  ocr2:
    build: .
    ports: ["8003:8002"]
  ocr3:
    build: .
    ports: ["8004:8002"]
  
  nginx:
    image: nginx
    ports: ["80:80"]
    # Load balance across ocr1, ocr2, ocr3
```

#### 4. Nginx Load Balancing
```nginx
upstream ocr_backends {
    least_conn;
    server ocr1:8002;
    server ocr2:8002;
    server ocr3:8002;
}

server {
    location / {
        proxy_pass http://ocr_backends;
    }
}
```

### Scaling Strategy

| Traffic Level | Strategy | Cost |
|---------------|----------|------|
| **Low (<100/day)** | Single Railway instance | $5-10/month |
| **Medium (<1000/day)** | Railway with auto-scaling | $20-40/month |
| **High (>1000/day)** | Multiple VPS + load balancer | $50-100/month |
| **Enterprise** | Kubernetes cluster | Custom |

### Monitoring

#### Health Check Endpoint
```bash
# Check service health
curl http://localhost:8002/api/v1/health

# Expected response:
# {"status":"healthy","matcher_loaded":true,...}
```

#### Logs
```bash
# Railway
railway logs

# Docker
docker logs riftbound-ocr

# Systemd
sudo journalctl -u riftbound-ocr -f
```

#### Metrics to Monitor
- ✅ Response time (30-60s is normal)
- ✅ Error rate (<5% acceptable)
- ✅ Memory usage (<2GB per worker)
- ✅ CPU usage (<80% sustained)
- ✅ Disk space (model cache grows)

---

## API Versioning

### Current Version
`v1` (November 2025)

### Future Versions

When breaking changes are introduced:
- New endpoints: `/api/v2/*`
- Old endpoints: `/api/v1/*` (maintained for 6 months)

### Version Headers
```http
GET /api/v1/process HTTP/1.1
X-API-Version: v1
```

---

## Support & Troubleshooting

### Common Issues

**1. "Service Unavailable" (503)**
- ✅ Check `/health` endpoint
- ✅ Verify card database loaded
- ✅ Check logs for errors

**2. Slow Processing (>120s)**
- ✅ Check if GPU enabled (faster)
- ✅ Verify image resolution (1080p optimal)
- ✅ Check CPU/memory usage

**3. Low Accuracy (<80%)**
- ✅ Check image quality
- ✅ Verify correct language (Chinese required)
- ✅ Check if cards are in database

**4. OOM Errors**
- ✅ Increase container memory limit
- ✅ Disable GPU mode
- ✅ Reduce parallel workers

### Debug Mode

Enable detailed logging:
```bash
LOG_LEVEL=DEBUG python start_server.py
```

### Contact & Resources

- **Documentation:** `/docs` (Swagger UI)
- **Repository:** https://github.com/yourusername/RiftboundOCR
- **Issues:** GitHub Issues

---

## Changelog

### Version 1.0.0 (November 2025)

**Features:**
- ✅ Position-based metadata extraction (96% accuracy)
- ✅ Player name extraction
- ✅ Deck name extraction
- ✅ Improved placement accuracy (100%)
- ✅ SSE streaming for batch processing
- ✅ Parallel processing (experimental)
- ✅ Complete API documentation

**Breaking Changes:**
- None (all new fields are optional)

**Metadata Fields Added:**
- `player` (NEW)
- `deck_name` (NEW)
- `legend_name_en` (NEW)

**Routes Added:**
- `/process-batch-stream` (SSE streaming)
- `/process-batch-fast` (parallel processing)

---

## License

See LICENSE file in repository

---

## Summary

This API provides complete OCR and card matching services for Chinese Riftbound decklists with:

- ✅ **6 API endpoints** (health, stats, single, batch, streaming, parallel)
- ✅ **96% metadata accuracy** (player, deck, placement, event, date)
- ✅ **93-96% card matching accuracy**
- ✅ **30-60s processing time** per image
- ✅ **Multiple hosting options** (Railway, Docker, VPS)
- ✅ **Production-ready** with health checks, logging, error handling
- ✅ **Scalable** horizontally with load balancing

**Ready to integrate!** 🚀

