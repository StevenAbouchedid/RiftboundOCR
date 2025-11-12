# Frontend Integration Checklist ✅

## Backend Response Structure (Confirmed Working)

```typescript
interface DecklistResponse {
  decklist_id: string;
  
  // ✅ METADATA - Always present (may have null values)
  metadata: {
    placement: number | null;  
    event: string | null;
    date: string | null;
  };
  
  // ✅ CARDS - Populated arrays
  legend: CardData[];          // 1 card
  main_deck: CardData[];       // ~40 cards  
  battlefields: CardData[];    // 3 cards
  runes: CardData[];           // 12 cards
  side_deck: CardData[];       // 0-8 cards
  
  // ✅ STATS - Always present
  stats: {
    total_cards: number;
    matched_cards: number;
    accuracy: number;  // 0-100
  };
}

interface CardData {
  name_cn: string;
  name_en: string;
  card_number: string;
  type_en: string;
  quantity: number;
  match_score: number;
  match_type: string;
  ocr_confidence: number;
  image_url_en: string;
}
```

## Integration Checklist

### 1. ✅ Fix SSE Event Access

**File:** `useUploadQueue.ts` or `page.tsx`

```typescript
// ❌ WRONG
case 'result':
  const deck = transformOCRToDeck(data);

// ✅ CORRECT
case 'result':
  const deck = transformOCRToDeck(data.decklist);
```

### 2. ✅ Display Metadata (Handle Nulls)

```typescript
function DeckMetadata({ metadata }) {
  return (
    <div className="metadata">
      {metadata.placement && (
        <div>Placement: #{metadata.placement}</div>
      )}
      {metadata.event && (
        <div>Event: {metadata.event}</div>
      )}
      {metadata.date && (
        <div>Date: {new Date(metadata.date).toLocaleDateString()}</div>
      )}
      {!metadata.placement && !metadata.event && !metadata.date && (
        <div className="text-gray-500">No metadata extracted</div>
      )}
    </div>
  );
}
```

### 3. ✅ Display Stats

```typescript
function DeckStats({ stats }) {
  return (
    <div className="stats">
      <div>Total Cards: {stats.total_cards}</div>
      <div>Matched: {stats.matched_cards}</div>
      <div className={stats.accuracy === 100 ? 'text-green-600' : 'text-yellow-600'}>
        Accuracy: {stats.accuracy.toFixed(1)}%
      </div>
    </div>
  );
}
```

### 4. ✅ Display Card Sections

```typescript
function DeckList({ decklist }) {
  return (
    <div>
      {/* Legend */}
      {decklist.legend.length > 0 && (
        <Section title="Legend" cards={decklist.legend} />
      )}
      
      {/* Main Deck */}
      {decklist.main_deck.length > 0 && (
        <Section title="Main Deck" cards={decklist.main_deck} />
      )}
      
      {/* Battlefields */}
      {decklist.battlefields.length > 0 && (
        <Section title="Battlefields" cards={decklist.battlefields} />
      )}
      
      {/* Runes */}
      {decklist.runes.length > 0 && (
        <Section title="Runes" cards={decklist.runes} />
      )}
      
      {/* Side Deck */}
      {decklist.side_deck.length > 0 && (
        <Section title="Side Deck" cards={decklist.side_deck} />
      )}
    </div>
  );
}

function Section({ title, cards }) {
  const totalCards = cards.reduce((sum, card) => sum + card.quantity, 0);
  
  return (
    <div className="section">
      <h3>{title} ({totalCards})</h3>
      {cards.map((card, idx) => (
        <div key={idx} className="card-row">
          <span className="quantity">{card.quantity}x</span>
          <span className="name">{card.name_en}</span>
          <span className="chinese">({card.name_cn})</span>
          {card.match_score < 100 && (
            <span className="match-score">{card.match_score.toFixed(0)}%</span>
          )}
        </div>
      ))}
    </div>
  );
}
```

## Testing Steps

### 1. Upload an Image

```typescript
// Should receive:
{
  "decklist_id": "uuid",
  "metadata": { placement: null, event: null, date: null },
  "legend": [...],
  "main_deck": [...],
  "battlefields": [...],
  "runes": [...],
  "side_deck": [...],
  "stats": { total_cards: 24, matched_cards: 24, accuracy: 100 }
}
```

### 2. Verify Console Output

Add debugging:
```typescript
console.log('Received decklist:', decklist);
console.log('Metadata:', decklist.metadata);
console.log('Stats:', decklist.stats);
console.log('Card counts:', {
  legend: decklist.legend.length,
  main_deck: decklist.main_deck.length,
  battlefields: decklist.battlefields.length,
  runes: decklist.runes.length,
  side_deck: decklist.side_deck.length
});
```

### 3. Expected Behavior

- ✅ Cards are displayed in all sections
- ✅ Stats show accuracy percentage
- ✅ Metadata shows when available (or shows "No metadata")
- ✅ No "undefined" or "Cannot read property" errors

## Common Issues

### Issue: Empty Arrays

**Symptom:** All card arrays are empty `[]`
**Cause:** Frontend accessing `data` instead of `data.decklist` in SSE handler
**Fix:** Change to `data.decklist`

### Issue: Metadata Undefined Error

**Symptom:** `Cannot read properties of undefined (reading 'placement')`
**Cause:** Frontend trying to access metadata before checking if it exists
**Fix:** Use optional chaining: `metadata?.placement`

### Issue: Stats Not Showing

**Symptom:** Stats object is undefined
**Cause:** Backend wasn't calculating stats (now fixed)
**Fix:** Backend now always sends stats ✅

## Backend Endpoints

### Process Single Image
```
POST http://localhost:8002/api/v1/process
Content-Type: multipart/form-data

Body: { file: <image> }
```

### Health Check
```
GET http://localhost:8002/api/v1/health
```

### Service Stats
```
GET http://localhost:8002/api/v1/stats
```

---

**Backend Status:** ✅ Running & Working  
**Response Format:** ✅ Correct  
**Data Availability:** ✅ Cards, Stats, Metadata (may be null)

**Next Step:** Update frontend to use `data.decklist` and display all fields! 🚀

