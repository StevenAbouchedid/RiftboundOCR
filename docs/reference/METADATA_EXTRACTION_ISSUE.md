# Metadata Extraction Issue

## 🔍 Current Status

### Backend IS Extracting Metadata ✅
The parser (`src/ocr/parser.py` lines 214-250) extracts:
- **placement** - From text containing '排名' or standalone numbers
- **event** - From text containing '区域公开赛' or '赛区'
- **date** - From YYYY-MM-DD patterns
- **legend_name** - From known legend names
- **player** - Not currently extracted (always None)

### Schema Definition ✅
`DecklistMetadata` (src/models/schemas.py):
```python
{
    "placement": Optional[int],
    "event": Optional[str],
    "date": Optional[str]
}
```

### Current Problem ❌
Metadata extraction **returns None** for test images:
```
[Stage 0] Extracting metadata...
  Placement: None
  Event: None
  Date: None
```

This means metadata **IS being sent** to frontend, just with null/empty values.

## 🐛 Why Metadata Isn't Being Extracted

### 1. Limited OCR Area
```python
# Only searches top 20% of image
metadata_crop = img.crop((0, 0, width, int(height * 0.2)))
```

### 2. Strict Pattern Matching
The parser looks for:
- **Placement**: Text containing '排名' OR standalone numbers ≤3 digits
- **Event**: Text containing '区域公开赛' OR '赛区'  
- **Date**: YYYY-MM-DD format only
- **Legend**: Hardcoded list of 8 legend names only

### 3. Example Test Image Format
Your test images may have:
- Metadata in different locations
- Different date formats
- Different event naming patterns
- Placement numbers not matching the pattern

## 🔧 Solutions

### Option 1: Expand Metadata Extraction (Better OCR)

Update `parse_with_two_stage()` in `src/ocr/parser.py`:

```python
# Expand search area to top 30%
metadata_crop = img.crop((0, 0, width, int(height * 0.3)))

# More flexible patterns
for text in texts:
    # Match more placement patterns
    if any(word in text for word in ['排名', '名次', '#', 'rank']):
        match = re.search(r'\d+', text)
        if match and not result.get('placement'):
            result['placement'] = int(match.group())
    
    # More flexible date formats
    elif re.search(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', text):
        date_match = re.search(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', text)
        result['date'] = date_match.group().replace('/', '-')
    
    # Capture any text with '赛' (competition/tournament)
    elif '赛' in text and len(text) > 3:
        if not result.get('event'):
            result['event'] = text
```

### Option 2: Frontend Provides Default/Fallback Values

If backend returns null metadata, frontend can:
- Show "Event not specified" 
- Show "Date unknown"
- Hide placement if not available
- Allow user to manually enter metadata

### Option 3: Add Manual Metadata Fields to Upload

Allow users to provide metadata when uploading:
```typescript
interface UploadMetadata {
    event?: string;
    date?: string;
    placement?: number;
    player?: string;
}
```

Then merge with OCR-extracted metadata.

## 📊 Check Current Response

Test what metadata is actually being returned:

```powershell
# Using curl or PowerShell
curl http://localhost:8002/api/v1/process -F "file=@test_images/deck.jpg" | jq .metadata
```

Expected response:
```json
{
  "placement": null,
  "event": null,
  "date": null
}
```

Or possibly with values if OCR found them:
```json
{
  "placement": 92,
  "event": "第一赛季区域公开赛-杭州赛区",
  "date": "2025-09-13"
}
```

## ✅ Frontend Should Handle This

Your frontend **should already be receiving** the metadata field, just with null values. Check your frontend code:

```typescript
// Backend is sending this:
{
  decklist_id: "uuid",
  metadata: {
    placement: null,  // ← These are being sent!
    event: null,
    date: null
  },
  legend: [...],
  ...
}

// Frontend should handle nulls gracefully:
{event && <div>Event: {event}</div>}
{placement && <div>Placement: #{placement}</div>}
{date && <div>Date: {date}</div>}
```

## 🎯 Recommended Fix

**For now:** Update your frontend to **display metadata when available**, with fallbacks for null values.

**Later:** Improve metadata extraction in the backend to handle more image formats and patterns.

---

**Status:** Backend sends metadata ✅ | Values are null ⚠️ | Frontend needs to display it 📋

