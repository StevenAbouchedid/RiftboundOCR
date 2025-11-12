# SSE Streaming Result Event - Quick Fix

## 🐛 Bug: `Cannot read properties of undefined (reading 'legend')`

## 🔧 Fix

The SSE `result` event has **nested data**. Access `data.decklist`, not `data` directly.

### Result Event Structure:
```json
{
  "index": 2,
  "filename": "deck3.jpg",
  "decklist": {           // ← Access THIS
    "legend": [...],
    "main_deck": [...],
    "battlefields": [...],
    "runes": [...],
    "side_deck": [...],
    "stats": {...}
  }
}
```

### ❌ Wrong:
```typescript
case 'result':
  const deck = transformOCRToDeck(data);  // ERROR: data has no 'legend'
```

### ✅ Correct:
```typescript
case 'result':
  const deck = transformOCRToDeck(data.decklist);  // ✅ Use nested 'decklist'
```

## 📝 Files to Fix

**Find this pattern in your code:**
- `useUploadQueue.ts` (around line 120)
- `page.tsx` (around line 43)
- `ocrUtils.ts` (in transformOCRToDeck function)

**Change:**
```typescript
// Before:
onResult(eventData) { transformOCRToDeck(eventData) }

// After:
onResult(eventData) { transformOCRToDeck(eventData.decklist) }
```

## ✅ Test

Add logging to verify:
```typescript
case 'result':
  console.log('Event data:', eventData);
  console.log('Has decklist?', eventData.decklist);  // Should be object
  const deck = transformOCRToDeck(eventData.decklist);
```

That's it! The OCR backend sends `decklist` nested inside the result event.


