# RiftboundOCR API Routes - Frontend Integration Guide

## 🎯 Service Overview

**RiftboundOCR is a SEPARATE microservice from the main Riftbound Top Decks API.**

- **Main API:** `http://localhost:8000` - Handles deck storage, user management, tournaments, etc.
- **OCR Service:** `http://localhost:8002` - Dedicated service for processing Chinese decklist screenshots

### Why Separate?

The OCR service requires heavy ML libraries (PaddleOCR, EasyOCR, PyTorch) and takes 30-60 seconds to process images. Keeping it separate ensures:
- Main API stays fast and lightweight
- OCR can be scaled independently
- Different deployment strategies (main on Vercel, OCR on Railway)

---

## 🏃 How to Run the Service Locally

### Prerequisites

- **Python 3.11 or 3.12** (NOT 3.13 - compatibility issues with ML libraries)
- **2-4GB free RAM** (for OCR models)
- **~3GB disk space** (for model downloads on first run)

### Quick Setup (5 minutes)

**Step 1: Clone and Navigate**
```bash
cd RiftboundOCR
```

**Step 2: Create Virtual Environment**
```bash
# Create venv
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

**Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Step 4: Create Environment File**
```bash
# Copy example file
copy env.example .env    # Windows
cp env.example .env      # Mac/Linux

# Edit .env if needed (defaults work for local dev)
```

**Step 5: Start the Service**
```bash
# Simple way
python start_server.py

# Or use the run script (includes setup checks)
python run_local.py
```

**Step 6: Verify It's Running**
```bash
# In another terminal
python test_local.py --quick
```

### Expected Output

```
============================================================
🚀 RiftboundOCR Service v1.0.0
============================================================
Host: 0.0.0.0:8002
Debug: True
GPU: False
============================================================
INFO:     Started server process [12948]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
```

### First Run Notes

⏱️ **First startup takes 2-3 minutes** as PaddleOCR downloads Chinese OCR models (~2-3GB). Subsequent runs are instant.

### Quick Verification

Visit these URLs in your browser:
- **Service Health:** http://localhost:8002/api/v1/health
- **API Docs:** http://localhost:8002/docs
- **Service Stats:** http://localhost:8002/api/v1/stats

You should see:
```json
{
  "status": "healthy",
  "service": "RiftboundOCR Service",
  "version": "1.0.0",
  "matcher_loaded": true,
  "total_cards_in_db": 322
}
```

### Troubleshooting Setup

**Python Version Wrong?**
```bash
# Check version
python --version

# Must be 3.11 or 3.12
# If wrong, install correct version from python.org
```

**Port Already in Use?**
```bash
# Edit .env file and change:
SERVICE_PORT=8003
```

**Windows DLL Errors?**
```bash
# Download and install Visual C++ Redistributable
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

**Dependencies Won't Install?**
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

---

## 📡 Base URLs

### Local Development
- **OCR Service:** `http://localhost:8002/api/v1`
- **Main API:** `http://localhost:8000/api` (your existing backend)

### Production
- **OCR Service:** `https://your-railway-domain.up.railway.app/api/v1`
- **Main API:** `https://riftbound-top-decks.vercel.app/api` (your existing backend)

---

## 🛣️ Available Endpoints

### 1. Health Check
**Check if the OCR service is running and ready**

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "RiftboundOCR Service",
  "version": "1.0.0",
  "matcher_loaded": true,
  "total_cards_in_db": 322
}
```

**Use Case:** Check service health before allowing users to upload images

---

### 2. Service Statistics
**Get information about OCR capabilities**

```http
GET /api/v1/stats
```

**Response:**
```json
{
  "matcher": {
    "total_cards": 322,
    "base_names": 306,
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

**Use Case:** Display supported formats and limits in your upload UI

---

### 3. Process Single Image ⭐ **PRIMARY ENDPOINT**
**Upload a Chinese decklist screenshot and get structured English card data**

```http
POST /api/v1/process
Content-Type: multipart/form-data
```

**Request Body:**
- `file` - Image file (JPG/PNG, max 10MB)

**Processing Time:** 30-60 seconds ⏱️

**Response:**
```json
{
  "decklist_id": "550e8400-e29b-41d4-a716-446655440000",
  "cards": {
    "legend": [
      {
        "name_cn": "无极剑圣",
        "name_en": "Wuju Bladesman - Starter",
        "card_number": "OGS·019/024",
        "type_en": "Legend",
        "quantity": 1,
        "match_score": 100,
        "match_type": "exact_full",
        "image_url_en": "https://..."
      }
    ],
    "main_deck": [
      {
        "name_cn": "小守护者",
        "name_en": "Clockwork Keeper",
        "card_number": "OGN·044/298",
        "type_en": "Unit",
        "quantity": 3,
        "match_score": 88.89,
        "match_type": "fuzzy_base_name",
        "image_url_en": "https://..."
      }
      // ... more cards
    ],
    "battlefields": [...],
    "runes": [...],
    "side_deck": [...]
  },
  "stats": {
    "total_cards": 63,
    "matched_cards": 59,
    "accuracy": 93.65,
    "unmatched_count": 4,
    "processing_time_seconds": 45.2
  },
  "metadata": {
    "player": null,
    "legend_name": null,
    "event": null,
    "date": null,
    "placement": null
  }
}
```

**Use Case:** Main decklist upload workflow

---

### 4. Batch Processing
**Process multiple decklist images at once**

```http
POST /api/v1/process-batch
Content-Type: multipart/form-data
```

**Request Body:**
- `files[]` - Array of image files (max 5 per batch)

**Processing Time:** 30-60 seconds per image

**Response:**
```json
{
  "total": 3,
  "successful": 3,
  "failed": 0,
  "average_accuracy": 94.2,
  "results": [
    {
      "decklist_id": "...",
      "cards": {...},
      "stats": {...}
    }
    // ... more results
  ]
}
```

**Use Case:** Bulk import functionality for events/tournaments

---

### 5. Process and Save to Main API
**Process image AND automatically save to main Riftbound API**

```http
POST /api/v1/process-and-save
Content-Type: multipart/form-data
```

**Request Body:**
- `file` - Image file (JPG/PNG)
- `owner` - Player name (string, optional, default: "Unknown")
- `format_id` - Format ID from main API (integer, optional, default: 1)

**Response:**
```json
{
  "id": 123,
  "name": "Wuju Bladesman Deck",
  "owner": "PlayerName",
  "format_id": 1,
  "legend_id": 45,
  "main_deck": [...],
  "side_deck": [...],
  "created_at": "2025-11-12T10:30:00Z",
  "ocr_stats": {
    "accuracy": 93.65,
    "matched_cards": 59,
    "total_cards": 63
  }
}
```

**Requirements:**
- Main API must be configured (`MAIN_API_URL` environment variable)
- Automatically resolves card IDs by matching card numbers with main API
- Creates deck record in main database

**Use Case:** One-step upload workflow (process + save)

---

## 🚨 Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### Common Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `400` | Bad Request | Invalid file type, file too large |
| `503` | Service Unavailable | OCR matcher not initialized, main API not configured |
| `500` | Internal Server Error | Processing failed, OCR error |

### Example Errors

**Invalid File Type:**
```json
{
  "detail": "File must be an image (JPG/PNG)"
}
```

**File Too Large:**
```json
{
  "detail": "File size (15.3MB) exceeds maximum (10MB)"
}
```

**Service Not Ready:**
```json
{
  "detail": "Card matcher not initialized"
}
```

---

## 💻 Frontend Implementation Examples

### React Example - Single Image Upload

```javascript
import { useState } from 'react';

function DecklistUploader() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async (file) => {
    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8002/api/v1/process', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }
      
      const data = await response.json();
      setResult(data);
      
      // Show success message
      alert(`Decklist processed! Accuracy: ${data.stats.accuracy}%`);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input 
        type="file" 
        accept="image/jpeg,image/png"
        onChange={(e) => handleUpload(e.target.files[0])}
        disabled={loading}
      />
      
      {loading && (
        <div className="loading">
          <p>Processing decklist... (30-60 seconds)</p>
          <progress />
        </div>
      )}
      
      {error && <p className="error">{error}</p>}
      
      {result && (
        <div className="results">
          <h3>Processed Decklist</h3>
          <p>Accuracy: {result.stats.accuracy}%</p>
          <p>Cards Found: {result.stats.total_cards}</p>
          
          <h4>Legend</h4>
          <ul>
            {result.cards.legend.map(card => (
              <li key={card.name_en}>{card.name_en} x{card.quantity}</li>
            ))}
          </ul>
          
          {/* Display main deck, battlefields, runes, side deck... */}
        </div>
      )}
    </div>
  );
}
```

### JavaScript Example - Process and Save

```javascript
async function uploadAndSaveDeck(imageFile, playerName, formatId = 1) {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('owner', playerName);
  formData.append('format_id', formatId);
  
  const response = await fetch('http://localhost:8002/api/v1/process-and-save', {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  const deck = await response.json();
  console.log('Deck created with ID:', deck.id);
  console.log('OCR Accuracy:', deck.ocr_stats.accuracy);
  
  return deck;
}
```

### TypeScript Types

```typescript
interface DecklistResponse {
  decklist_id: string;
  cards: {
    legend: Card[];
    main_deck: Card[];
    battlefields: Card[];
    runes: Card[];
    side_deck: Card[];
  };
  stats: {
    total_cards: number;
    matched_cards: number;
    accuracy: number;
    unmatched_count: number;
    processing_time_seconds: number;
  };
  metadata: {
    player: string | null;
    legend_name: string | null;
    event: string | null;
    date: string | null;
    placement: string | null;
  };
}

interface Card {
  name_cn: string;
  name_en: string;
  card_number: string;
  type_en: string;
  quantity: number;
  match_score: number;
  match_type: string;
  image_url_en: string;
}
```

---

## 🎨 UX Recommendations

### File Upload
- **Accept:** JPG, PNG only
- **Max Size:** 10MB
- **Validation:** Check file type and size before upload

### Loading State
- **Show:** Progress indicator with estimated time (30-60 seconds)
- **Message:** "Processing Chinese decklist screenshot..."
- **Tip:** Recommend users not to navigate away during processing

### Results Display
- **Show Accuracy:** Highlight if accuracy is below 90%
- **Allow Review:** Let users review and manually correct card matches
- **Visual Feedback:** Use green for high confidence (>90), yellow for medium (70-90), red for low (<70)

### Error Handling
```javascript
// Example error handling
const ERROR_MESSAGES = {
  'File must be an image': 'Please upload a JPG or PNG image',
  'File size': 'Image is too large. Maximum size is 10MB',
  'Card matcher not initialized': 'OCR service is starting up. Please try again in a moment',
  'Failed to create deck': 'Could not save deck. Please try again or contact support'
};

function getUserFriendlyError(apiError) {
  for (const [key, message] of Object.entries(ERROR_MESSAGES)) {
    if (apiError.includes(key)) return message;
  }
  return 'An unexpected error occurred. Please try again.';
}
```

---

## 🔌 Integration Workflow

### Option 1: Two-Step (Frontend Controls)

1. **Frontend → OCR Service:** Upload image to `/api/v1/process`
2. **Frontend receives:** Structured card data
3. **Frontend → Main API:** Save deck with card data to main backend
4. **User:** Can review/edit cards before saving

**Best for:** Allowing user review and manual corrections

### Option 2: One-Step (OCR Service Handles)

1. **Frontend → OCR Service:** Upload image to `/api/v1/process-and-save`
2. **OCR Service → Main API:** Automatically saves deck
3. **Frontend receives:** Complete deck with database ID

**Best for:** Quick upload without review step

---

## 🔧 Configuration

### Frontend Environment Variables

```bash
# .env.local (for frontend)
VITE_OCR_SERVICE_URL=http://localhost:8002/api/v1  # Local
# VITE_OCR_SERVICE_URL=https://your-railway-domain.up.railway.app/api/v1  # Production

VITE_MAIN_API_URL=http://localhost:8000/api  # Your existing backend
```

### Usage in Code

```javascript
const OCR_API_URL = import.meta.env.VITE_OCR_SERVICE_URL;
const MAIN_API_URL = import.meta.env.VITE_MAIN_API_URL;

// Use OCR service for image processing
fetch(`${OCR_API_URL}/process`, {...});

// Use main API for everything else
fetch(`${MAIN_API_URL}/decks`, {...});
```

---

## 📊 Performance Expectations

| Metric | Expected Value |
|--------|---------------|
| Processing Time | 30-60 seconds per image |
| Accuracy | 93%+ on clear screenshots |
| Concurrent Requests | 1-2 (CPU-bound, sequential) |
| Max File Size | 10MB |
| Batch Size | 5 images per request |

### Optimization Tips

- ✅ **Do:** Show progress indicator during upload
- ✅ **Do:** Compress images on client before upload (maintain quality)
- ✅ **Do:** Implement request queuing for multiple uploads
- ❌ **Don't:** Allow concurrent uploads from same user (will slow down)
- ❌ **Don't:** Upload images larger than 10MB

---

## 🐛 Troubleshooting

### Service Not Responding

```javascript
// Health check before upload
async function checkOCRServiceHealth() {
  try {
    const response = await fetch('http://localhost:8002/api/v1/health');
    const data = await response.json();
    return data.status === 'healthy';
  } catch {
    return false;
  }
}

// Use in UI
if (await checkOCRServiceHealth()) {
  // Show upload button
} else {
  // Show "Service temporarily unavailable" message
}
```

### Accuracy Too Low

If accuracy is below 90%:
1. Check image quality (resolution, blur, lighting)
2. Verify screenshot shows full decklist
3. Ensure text is in Chinese (not English)
4. Consider manual review/correction flow in UI

---

## 📞 Support

- **OCR Service Issues:** Check `http://localhost:8002/api/v1/health`
- **Main API Issues:** Check your existing backend health endpoint
- **Card Matching Issues:** Review card mappings in `src/ocr/data/card_mappings_final.csv`

---

## 🚀 Quick Start Checklist

- [ ] Verify OCR service is running on port 8002
- [ ] Check health endpoint returns `"status": "healthy"`
- [ ] Configure `VITE_OCR_SERVICE_URL` in frontend
- [ ] Add file upload input (accept JPG/PNG, max 10MB)
- [ ] Implement loading state with 30-60s timeout
- [ ] Display results with accuracy percentage
- [ ] Handle errors gracefully with user-friendly messages
- [ ] Test with sample Chinese decklist screenshots

---

**Remember:** This is a **separate service** from your main backend. Both must be running for the full upload workflow to work!

