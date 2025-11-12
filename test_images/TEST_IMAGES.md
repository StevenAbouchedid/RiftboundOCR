# Test Images

## Available Test Images ✅

We have **7 real Chinese decklist screenshots** from Hangzhou Season 1 tournament:

```
✅ Screenshot_20251106_021827_WeChat.jpg (928KB)
✅ Screenshot_20251106_021842_WeChat.jpg (935KB)
✅ Screenshot_20251106_034515_WeChat.jpg (964KB)
✅ Screenshot_20251106_034527_WeChat.jpg (973KB)
✅ Screenshot_20251106_040031_WeChat.jpg (968KB)
✅ Screenshot_20251106_040048_WeChat.jpg (1.1MB)
✅ Screenshot_20251106_040114_WeChat.jpg (950KB)
```

**Total:** 7 images (~6.7MB)  
**Source:** Hangzhou Season 1 Regional Tournament  
**Format:** WeChat screenshots (JPG)  
**Resolution:** High-quality (suitable for OCR)

---

## Usage

### Test Single Image

```bash
# Using Python API
from src.ocr.parser import parse_decklist
from src.ocr.matcher import match_cards

result = parse_decklist('test_images/Screenshot_20251106_021827_WeChat.jpg')
matched = match_cards(result)
print(f"Accuracy: {matched['stats']['accuracy']}%")
```

### Test via API

```bash
# Start server
python src/main.py

# Test with curl
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@test_images/Screenshot_20251106_021827_WeChat.jpg"
```

### Run Validation

```bash
# Process all test images and generate report
python tests/validate_accuracy.py
```

---

## Expected Results

Based on similar images tested during development:

- **OCR Accuracy:** 95-98% for card names
- **Quantity Detection:** 99-100% accuracy
- **Overall Match Rate:** 90-95%
- **Processing Time:** 30-60 seconds per image

---

## Notes

- Images are from real tournament decklists
- All images contain Chinese card names
- Some may have metadata (placement, event, date)
- Perfect for end-to-end testing

---

## Adding More Images

To add more test images:

1. Place JPG/PNG files in this directory
2. Recommended naming: `deck_name_tournament.jpg`
3. Ensure images are clear and well-lit
4. Resolution: 1080p or higher recommended




