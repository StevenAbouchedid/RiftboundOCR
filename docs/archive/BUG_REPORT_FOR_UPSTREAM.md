# Bug Report: Missing Metadata Fields After Integration

## Summary
After integrating the OCR extraction logic, we're encountering missing/incomplete metadata extraction. The parser extracts `player` field internally but it's not passed through to the API response schema. Additionally, no `deck_name` field exists.

## Environment
- **Python:** 3.12.0
- **PaddleOCR:** 2.9.1
- **EasyOCR:** 1.7.2
- **OS:** Windows 10
- **Image Format:** JPG (WeChat screenshots)

## Issue 1: Player Name Not in API Response

### What Happens
The parser (`parse_with_two_stage`) initializes `player: None` but never extracts it:

```python
result = {
    'player': None,  # ← Initialized but never populated
    'legend_name': None,
    'event': None,
    'date': None,
    'placement': None,
    ...
}
```

The matcher passes `player` to metadata:
```python
matched = {
    'metadata': {
        'player': parsed_decklist.get('player'),  # ← Passed but always None
        ...
    }
}
```

But `DecklistMetadata` schema doesn't include `player` field, so it's **silently dropped** from API response.

### Expected
API response should include:
```json
{
  "metadata": {
    "player": "PlayerName123",  // ← Missing
    "deck_name": "Master Yi Control",  // ← Doesn't exist
    "placement": 92,
    "event": "Season 1 Finals",
    "date": "2025-11-01"
  }
}
```

### Actual
```json
{
  "metadata": {
    "placement": null,
    "event": null,
    "date": null
    // No player or deck_name fields
  }
}
```

## Issue 2: Metadata Extraction Always Returns Null

### Console Output
```
[Stage 0] Extracting metadata...
  Placement: None
  Event: None
  Date: None
```

### Extraction Logic
Current implementation searches **top 20% of image only**:
```python
metadata_crop = img.crop((0, 0, width, int(height * 0.2)))
```

Pattern matching is very strict:
- **Placement:** Requires '排名' text or standalone numbers ≤3 digits
- **Event:** Requires '区域公开赛' OR '赛区'
- **Date:** Only YYYY-MM-DD format
- **Player:** No extraction logic at all

### Test Images
Using WeChat tournament screenshots with metadata visible at top, but extraction returns null for all fields.

## Issue 3: Missing Card in Main Deck

### Console Output
```
✗ MAIN DECK: 39 cards (expected: 40)
  3x 小守护者
  3x 强强魄罗
  2x 苍炎守护者
  2x 美味仙灵
  3x 竞技场新人
  3x 大副
  3x 亡花掠食者
  3x 中娅沙漏
  3x 蔑视
  3x 魅惑妖术
  2x 决斗架势
  3x 御衡守念
  3x 训练有素
  3x 万世催化石
```

Total: 39 cards (missing 1)

### Processing Output
```
Total card boxes across all sections: 25
Found 25 card boxes but standard deck should have ~63 cards
```

Consistently missing 1 card from main deck across multiple test images.

## Questions for Original Repo

1. **Was `player` field supposed to be extracted?** If so, where should the extraction logic be added in `parse_with_two_stage()`?

2. **Should `deck_name` exist?** Is it meant to be:
   - Extracted from images?
   - Generated from legend name + placement?
   - Provided manually by users?

3. **Metadata extraction patterns** - Are the current patterns (排名, 区域公开赛, YYYY-MM-DD) sufficient for most tournament screenshots, or should they be more flexible?

4. **Missing main deck card** - Any known issues with card box detection that might cause 39/40 detection rate?

## Code References

### Parser: `src/ocr/parser.py`
- Lines 199-212: Result structure initialization
- Lines 214-250: Metadata extraction logic
- Line 200: `'player': None` (never populated)

### Matcher: `src/ocr/matcher.py`
- Lines 193-199: Metadata passed through
- Line 194: `'player': parsed_decklist.get('player')`

### Schema: `src/models/schemas.py`
- Lines 48-63: `DecklistMetadata` class
- Missing: `player` and `deck_name` fields

## Additional Context

This is integrated into a deck aggregation platform where:
- **Player name** is required to attribute decks to players
- **Deck name** is required for deck identification/display
- **Event/date/placement** are used for tournament tracking

All other fields (cards, stats, accuracy) are working perfectly. Only metadata extraction has issues.

## Sample Image Available
Can provide sample WeChat tournament screenshot if needed for debugging.

---

**Priority:** High - Blocking frontend integration  
**Impact:** Cannot display deck metadata without these fields

