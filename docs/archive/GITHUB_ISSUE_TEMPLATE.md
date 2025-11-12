# Card Name Extraction Returns "N/A" for All Cards

## Environment
- **OS**: Windows 10/11
- **Python**: 3.12
- **PaddleOCR**: 2.9.1 (PP-OCRv4 Chinese models downloaded)
- **EasyOCR**: 1.7.2 (Chinese language pack)
- **Hardware**: CPU only (no GPU)

## Issue
The OCR service successfully processes images but **all card names return "N/A"** instead of extracting the actual Chinese text from Riftbound decklist screenshots.

## What's Working ✅
- FastAPI server running
- PaddleOCR and EasyOCR both initialized
- Card database loaded (322 Chinese↔English mappings)
- Metadata extraction (event name, date, placement)
- Section detection (legend, main_deck, battlefields, runes, side_deck)

## What's Broken ❌
Card name extraction from individual card boxes returns:
```python
{"chinese_name": "N/A", "quantity": 1}
```

**For ALL cards** in every section.

## Diagnostic Output
```
OCR DETECTED TEXT:

METADATA:
  {'placement': 2, 'event': '第一赛季区域公开赛-杭州赛区', 'date': '2025-09-13'}

LEGEND:
  - N/A (x1)      # Should be Chinese card name

MAIN_DECK:
  - N/A (x1)      # Should be Chinese card name

BATTLEFIELDS:
  - N/A (x1)      # Should be Chinese card name

RUNES:
  - N/A (x1)      # Should be Chinese card name

SIDE_DECK:
  - N/A (x1)      # Should be Chinese card name
```

**Match rate: 0/5 cards (0%)**

## Implementation

Using PaddleOCR for Chinese text (left 70% of card region) and EasyOCR for quantities (right 30%):

```python
class DecklistParser:
    def __init__(self, use_gpu: bool = False):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            use_gpu=use_gpu,
            show_log=False
        )
        self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=use_gpu)
    
    def _extract_card_data(self, section_image, region):
        # Extract card box
        x, y, w, h = region
        card_img = section_image[y:y+h, x:x+w]
        
        # Split into name (left 70%) and quantity (right 30%)
        name_region = card_img[:, :int(w * 0.7)]
        quantity_region = card_img[:, int(w * 0.7):]
        
        # OCR the name with PaddleOCR
        result = self.ocr.ocr(name_region, cls=True)
        # ⚠️ Returns "N/A" here
        
        # OCR quantity with EasyOCR
        qty_result = self.reader.readtext(quantity_region)
        # Also returns "N/A"
```

## Test Image
- **Format**: WeChat screenshot (JPG)
- **Content**: Chinese Riftbound decklist
- **Language**: Simplified Chinese
- **Image name**: `Screenshot_20251106_021827_WeChat.jpg`

## Questions

1. **Is the 70/30 split correct for Riftbound card layout?**
   - Where is the card name positioned?
   - Where is the quantity number?

2. **Do WeChat screenshots need special preprocessing?**
   - Color space conversion?
   - Resolution scaling?
   - Contrast enhancement?

3. **Are the PaddleOCR parameters correct?**
   - Should `use_angle_cls` be True?
   - Are there detection/recognition thresholds to adjust?
   - Does the image need preprocessing before OCR?

4. **How should card boxes be detected?**
   - Are there visual separators between cards?
   - What method should be used (contours, template matching, fixed grid)?

5. **Can you provide:**
   - Example images that work correctly?
   - Expected OCR output for reference images?
   - Debugging visualization code?
   - Layout specifications for Riftbound decklists?

## Expected vs Actual

### Expected Card Names:
```
安妮, 汹涌烈焰 (Annie, Fiery)
烈火风暴 (Firestorm)
易, 禅心大道 (Yi, Meditative)
拉克丝, 明丽光华 (Lux, Illuminated)
盖伦, 身经百战 (Garen, Rugged)
```

### Actual OCR Output:
```
N/A
N/A
N/A
N/A
N/A
```

## Help Needed

The metadata extraction proves that PaddleOCR CAN read Chinese text from the image (event name extracts correctly). But card name extraction from individual card boxes always returns "N/A".

**Any guidance on:**
- Debugging why text extraction fails for card names specifically
- Correct image preprocessing for card regions
- Proper PaddleOCR configuration for this use case
- Alternative detection/extraction strategies

Thank you! 🙏



