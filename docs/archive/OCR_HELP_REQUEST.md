# 🆘 Help Request: RiftboundOCR Card Name Extraction Issue

**TL;DR**: OCR service successfully runs and processes images, but all Chinese card names return "N/A" instead of actual text. Metadata extraction WORKS (proves PaddleOCR can read Chinese), but individual card name extraction fails. Need guidance on proper card detection/extraction for Riftbound decklist format.

---

## 📊 Current Status

### ✅ What's Working (Environment Confirmed Good)

- **Server**: FastAPI running on http://localhost:8002
- **Dependencies**: PaddleOCR 2.9.1, EasyOCR 1.7.2, PyTorch 2.9.1 (CPU)
- **Models**: PP-OCRv4 Chinese models downloaded (detection, recognition, classification)
- **Database**: 322 Chinese↔English card mappings loaded
- **Image Processing**: Images accepted, processed in ~8.58 seconds
- **Metadata Extraction**: ✅ **WORKS CORRECTLY** - Extracts `'event': '第一赛季区域公开赛-杭州赛区'`
- **Section Detection**: All sections identified (legend, main_deck, battlefields, runes, side_deck)

**Key Evidence**: Metadata extraction proves PaddleOCR CAN read Chinese text from the same image!

### ❌ The Problem

**All card names return "N/A" with quantity "1"**

```
OCR DETECTED TEXT:

METADATA:
  {'placement': 2, 'event': '第一赛季区域公开赛-杭州赛区', 'date': '2025-09-13'} ← WORKS! ✅

LEGEND:
  - N/A (x1)  ← FAILS ❌

MAIN_DECK:
  - N/A (x1)  ← FAILS ❌

BATTLEFIELDS:
  - N/A (x1)  ← FAILS ❌

RUNES:
  - N/A (x1)  ← FAILS ❌

SIDE_DECK:
  - N/A (x1)  ← FAILS ❌
```

**Result**: 0% match rate (0/5 cards matched to database)

**Expected**: Should extract Chinese card names like:
- `安妮, 汹涌烈焰` (Annie, Fiery)
- `烈火风暴` (Firestorm)
- `易, 禅心大道` (Yi, Meditative)
- `拉克丝, 明丽光华` (Lux, Illuminated)
- `盖伦, 身经百战` (Garen, Rugged)

---

## 🔧 Environment

- **OS**: Windows 10/11
- **Python**: 3.12
- **PyTorch**: 2.9.1+cpu
- **PaddleOCR**: 2.9.1
- **EasyOCR**: 1.7.2
- **OpenCV**: 4.10.0.84
- **Image Source**: WeChat screenshot (JPG)
- **Hardware**: CPU only (no GPU)

---

## 💻 Current Implementation

### Parser Architecture

```python
class DecklistParser:
    def __init__(self, use_gpu: bool = False):
        # PaddleOCR for Chinese text
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            use_gpu=use_gpu,
            show_log=False
        )
        
        # EasyOCR as fallback
        self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=use_gpu)
    
    def parse(self, image_path: str) -> Dict:
        image = cv2.imread(image_path)
        
        # 1. Extract metadata (✅ WORKS)
        metadata = self._extract_metadata(image)
        
        # 2. Detect sections (✅ WORKS)
        sections = self._detect_sections(image)
        
        # 3. For each section:
        #    - Detect card boxes
        #    - Extract card data (❌ FAILS - returns "N/A")
        
        return result
```

### Card Extraction Logic (Where It Fails)

```python
def _extract_card_data(self, section_image, region):
    """Extract Chinese name + quantity from card box"""
    x, y, w, h = region
    card_img = section_image[y:y+h, x:x+w]
    
    # Split card region: 70% name (left) | 30% quantity (right)
    name_region = card_img[:, :int(w * 0.7)]
    quantity_region = card_img[:, int(w * 0.7):]
    
    # OCR the name with PaddleOCR
    result = self.ocr.ocr(name_region, cls=True)
    # ⚠️ Returns "N/A" here
    
    # OCR quantity with EasyOCR  
    qty_result = self.reader.readtext(quantity_region)
    # Also returns "N/A"
    
    return {"chinese_name": "N/A", "quantity": 1}
```

---

## 🤔 Suspected Issues

1. **Card box detection** - Not finding correct regions?
2. **70/30 split assumption** - Wrong layout for Riftbound cards?
3. **OCR parameters** - Thresholds too strict?
4. **Image preprocessing** - Card regions need different processing than metadata?
5. **WeChat screenshots** - Special format issues?

**Contradiction**: If metadata extraction works with the same PaddleOCR instance on the same image, why don't card names work?

---

## ❓ Questions for Original Repo Team

### Layout & Detection
1. **What is the correct Riftbound decklist layout?**
   - Where are card names positioned relative to quantities?
   - Is 70/30 split correct, or should it be different?
   - Are there visual separators between cards?

2. **How should card boxes be detected?**
   - Contour detection?
   - Template matching?
   - Fixed grid based on section size?
   - Line detection for separators?

### OCR Configuration
3. **What PaddleOCR parameters work for Riftbound card names?**
   - Should `use_angle_cls` be True/False?
   - Are there detection/recognition thresholds to adjust?
   - Does the image need preprocessing (contrast, resize, denoise)?

4. **Do WeChat screenshots need special handling?**
   - Color space conversion?
   - DPI/resolution adjustments?
   - Specific preprocessing steps?

### Debugging
5. **How to debug this effectively?**
   - Code to visualize detected card boxes?
   - Way to see raw PaddleOCR output before filtering?
   - How to check if text is detected but filtered out by confidence?

### Reference Materials
6. **Can you provide:**
   - ✅ Example images that work correctly?
   - ✅ Expected OCR output for those images?
   - ✅ Reference implementation or working code?
   - ✅ Riftbound decklist format specifications?

---

## 📎 Test Materials Attached

1. **Sample Image**: `test_images/Screenshot_20251106_021827_WeChat.jpg`
   - Standard WeChat screenshot
   - Chinese Riftbound decklist
   - Event: 第一赛季区域公开赛-杭州赛区
   - Multiple sections with cards

2. **Diagnostic Script**: `debug_ocr.py`
   - Shows OCR detected text
   - Displays matching attempts
   - Samples database cards
   - Can be run to reproduce issue

3. **Implementation Files**:
   - `src/ocr/parser.py` - Parser with card extraction logic
   - `src/ocr/matcher.py` - Matching logic (ready to use once extraction works)
   - `resources/card_mappings_final.csv` - 322 card database

4. **Full Diagnostic Output**: See "Current Status" section above

---

## 🎯 What Success Looks Like

```
OCR DETECTED TEXT:

LEGEND:
  - 安妮, 汹涌烈焰 (x1)  ✅

MAIN_DECK:
  - 烈火风暴 (x3)  ✅
  - 易, 禅心大道 (x2)  ✅

Match Rate: 95%+ (cards found in database)
```

---

## 🚀 Ready to Test Fixes

Our environment is fully set up and working. We can:
- Test any suggested changes immediately
- Try different detection methods
- Adjust OCR parameters
- Run visualization/debugging code
- Test with different images

Just need guidance on:
1. Correct card detection approach for Riftbound format
2. Proper OCR parameters/preprocessing
3. Or reference working implementation to compare against

---

## 🙏 Summary

**We're SO CLOSE!** The infrastructure works perfectly:
- ✅ All dependencies installed
- ✅ Models downloaded
- ✅ Server running
- ✅ PaddleOCR reading Chinese (metadata proves it!)
- ✅ Card database loaded and ready

**One blocker**: Card name extraction from individual card boxes returns "N/A"

Any guidance on the correct Riftbound card detection/extraction approach would get us to 100% functional!

Thank you for any help! 🙏

---

## 📧 Contact & Repo

**Testing Environment**: Windows 10/11, Python 3.12, local development
**Response Time**: Can test suggested fixes within minutes
**Documentation**: Full technical docs available if needed

Looking forward to your guidance!



