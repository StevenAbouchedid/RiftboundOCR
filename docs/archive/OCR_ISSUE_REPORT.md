# RiftboundOCR - Card Name Detection Issue

## 🔍 Issue Summary

The OCR service successfully starts and processes images, but **all card names are being detected as "N/A"** instead of extracting the actual Chinese text from the decklist screenshots.

---

## ✅ What's Working

1. **Server**: FastAPI service running on http://localhost:8002
2. **Dependencies**: PaddleOCR (Chinese text) + EasyOCR (fallback) both initialized
3. **Card Database**: 322 cards loaded from CSV with Chinese→English mappings
4. **Image Processing**: Images are accepted and processed (8.58s processing time)
5. **Metadata Extraction**: Event info is correctly extracted (e.g., "第一赛季区域公开赛-杭州赛区")
6. **Section Detection**: All sections detected (legend, main_deck, battlefields, runes, side_deck)

---

## ❌ What's Not Working

**Card Name Extraction**: All card names return "N/A" with quantity "1"

### Diagnostic Output:

```
============================================================
OCR DETECTED TEXT
============================================================

METADATA:
  {'placement': 2, 'event': '第一赛季区域公开赛-杭州赛区', 'date': '2025-09-13'}

LEGEND:
  - N/A (x1)

MAIN_DECK:
  - N/A (x1)

BATTLEFIELDS:
  - N/A (x1)

RUNES:
  - N/A (x1)

SIDE_DECK:
  - N/A (x1)
```

**Result**: 0% match rate (0/5 cards matched to database)

---

## 📸 Test Image

- **Source**: WeChat screenshot of Chinese decklist
- **Format**: JPG (Screenshot_20251106_021827_WeChat.jpg)
- **Characteristics**:
  - Chinese text (Simplified)
  - Standard Riftbound card list format
  - Multiple sections (Legend, Main Deck, Battlefields, Runes, Side Deck)
  - Card names + quantities

---

## 🔧 Environment

- **OS**: Windows 10/11
- **Python**: 3.12
- **PyTorch**: 2.9.1+cpu (CPU only, no GPU)
- **PaddleOCR**: 2.9.1 with PP-OCRv4 Chinese models
- **EasyOCR**: 1.7.2 with Chinese language pack
- **OpenCV**: 4.10.0.84
- **Pillow**: 10.4.0

### Models Downloaded:
- ✅ `ch_PP-OCRv4_det_infer` (detection)
- ✅ `ch_PP-OCRv4_rec_infer` (recognition)
- ✅ `ch_ppocr_mobile_v2.0_cls_infer` (classification)

---

## 📝 Implementation Details

### Parser Architecture (`src/ocr/parser.py`)

```python
class DecklistParser:
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        
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
        # Load image
        image = cv2.imread(image_path)
        
        # Extract metadata (WORKS - returns correct event info)
        metadata = self._extract_metadata(image)
        
        # Detect sections (WORKS - finds all sections)
        sections = self._detect_sections(image)
        
        # For each section:
        #   - Detect card boxes
        #   - Extract card data (NAME + QUANTITY)
        #   ⚠️ THIS IS WHERE IT FAILS - returns "N/A"
        
        return result
```

### Key Functions:

1. **`_detect_card_boxes()`**: Detects individual card regions in each section
2. **`_extract_card_data()`**: Extracts Chinese name + quantity from each card box
   - **Uses PaddleOCR for name (left 70% of card)**
   - **Uses EasyOCR for quantity (right 30% of card)**
   - ⚠️ **Returns `{"chinese_name": "N/A", "quantity": 1}` for all cards**

---

## 🤔 Potential Causes

### 1. **Card Box Detection Issue**
- Boxes aren't being detected correctly
- Regions are empty or incorrectly sized

### 2. **Text Region Splitting Issue**
- The 70/30 split for name/quantity might not align with actual layout
- Text might be in different positions than expected

### 3. **OCR Configuration Issue**
- PaddleOCR parameters might need adjustment
- Detection/recognition thresholds too strict
- Image preprocessing not working for card names

### 4. **Image Format Issue**
- WeChat screenshots might have specific characteristics
- Resolution/DPI issues
- Color space or contrast problems

### 5. **Text Extraction Logic**
- The logic checking if OCR results are valid might be too strict
- Confidence thresholds rejecting valid text
- Text cleaning/filtering removing actual names

---

## 📊 Sample Cards in Database

The database has proper Chinese names:

```
1. 安妮, 汹涌烈焰 → Annie, Fiery
2. 烈火风暴 → Firestorm  
3. 焚烧 → Incinerate
4. 易, 禅心大道 → Yi, Meditative
5. 和风贤者 → Zephyr Sage
6. 拉克丝, 明丽光华 → Lux, Illuminated
7. 盖伦, 身经百战 → Garen, Rugged
8. 绅士决斗 → Gentlemen'S Duel
9. 易, 锋芒毕现 → Yi, Honed
10. 安妮, 野火丛生 → Annie, Stubborn
```

So matching **will work** once we extract the Chinese text correctly.

---

## 🆘 Questions for Original OCR Repo Team

### 1. **Is this a known issue with WeChat screenshots?**
   - Do they have special encoding/format?
   - Do they need preprocessing?

### 2. **How should card boxes be detected in standard Riftbound decklist images?**
   - What's the expected layout?
   - Are there visual separators between cards?
   - How are sections divided?

### 3. **What are the correct OCR parameters for Riftbound card names?**
   - PaddleOCR threshold settings?
   - Image preprocessing steps?
   - Resolution requirements?

### 4. **Is the 70/30 split (name/quantity) correct for Riftbound card layout?**
   - Where exactly is the card name positioned?
   - Where is the quantity number?
   - Are there visual boundaries?

### 5. **Are there any reference implementations or examples?**
   - Working code for similar Riftbound OCR?
   - Example images that work correctly?
   - Test suite or validation images?

### 6. **What debugging steps can help identify where the text extraction fails?**
   - How to visualize detected boxes?
   - How to see raw OCR output before filtering?
   - How to check if text is detected but filtered out?

---

## 🔬 Debugging Needed

To help diagnose, we need to:

1. **Visualize detected card boxes** - Are they in the right place?
2. **See raw OCR output** - Is PaddleOCR detecting ANY Chinese text?
3. **Check image preprocessing** - Are images being transformed correctly?
4. **Inspect confidence scores** - Is text being rejected due to low confidence?
5. **Test with reference images** - Does it work with "known good" images?

---

## 💡 Request

Could the original Riftbound OCR repo team provide:

1. ✅ **Working example images** that should extract correctly
2. ✅ **Expected OCR output** for those images
3. ✅ **Debugging visualization code** to see what's being detected
4. ✅ **Configuration guidance** for PaddleOCR parameters
5. ✅ **Layout specifications** for Riftbound decklist format

---

## 📎 Attachments

- `test_images/Screenshot_20251106_021827_WeChat.jpg` - Sample test image
- `debug_ocr.py` - Diagnostic script
- `src/ocr/parser.py` - Current parser implementation
- `resources/card_mappings_final.csv` - Card database (322 cards)

---

## 🎯 Success Criteria

We'll know it's working when:

1. ✅ Chinese card names are extracted (e.g., "安妮, 汹涌烈焰")
2. ✅ Quantities are detected correctly (e.g., "x3")
3. ✅ Match rate > 90% (cards found in database)
4. ✅ Processing time < 60 seconds per image

---

## 🙏 Current Status

- ⚠️ **Blocked**: Cannot proceed with production deployment until card name extraction works
- ✅ **Infrastructure**: All services running correctly
- ✅ **Matching**: Ready to match once Chinese text is extracted
- ❌ **Blocker**: Card name OCR returning "N/A" for all cards

---

**Thank you for any guidance or suggestions!** 🙏

The service is SO CLOSE to working - just need to crack the card name extraction issue!



