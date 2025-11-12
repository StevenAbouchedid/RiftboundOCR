# Frontend SSE Fix - Quick Guide

## 🐛 Error
```
TypeError: Cannot read properties of undefined (reading 'legend')
at transformOCRToDeck (ocrUtils.ts:82:39)
```

## 🔍 Root Cause
The SSE `result` event has **nested data**. Access `data.decklist`, not `data` directly.

## ✅ Backend Fixed (Nov 12, 2024)
The backend was also returning empty arrays due to incorrect data structure. This has been fixed in `src/ocr/matcher.py` - cards are now properly returned at the top level of the response.

## ✅ Solution

### Result Event Structure (from backend):
```json
{
  "index": 2,
  "filename": "deck3.jpg",
  "decklist": {           // ← OCR data is HERE
    "legend": [...],
    "main_deck": [...],
    "battlefields": [...],
    "runes": [...],
    "side_deck": [...],
    "stats": {...}
  }
}
```

### Fix in `useUploadQueue.ts` (around line 120):

**❌ Before:**
```typescript
case 'result':
  const deck = transformOCRToDeck(data);
```

**✅ After:**
```typescript
case 'result':
  const deck = transformOCRToDeck(data.decklist);
```

### Or in `page.tsx` (around line 47):

**❌ Before:**
```typescript
onFileComplete: (data) => {
  const deck = transformOCRToDeck(data);
}
```

**✅ After:**
```typescript
onFileComplete: (data) => {
  const deck = transformOCRToDeck(data.decklist);
}
```

## 🧪 Verify
Add logging to confirm structure:
```typescript
case 'result':
  console.log('Keys:', Object.keys(data));        // Should show: index, filename, decklist
  console.log('Has decklist?', data.decklist);    // Should be object
  const deck = transformOCRToDeck(data.decklist);
```

---

**That's it!** Change `data` → `data.decklist` wherever you call `transformOCRToDeck` with SSE event data.

