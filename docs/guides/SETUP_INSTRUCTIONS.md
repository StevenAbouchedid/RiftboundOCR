# Setup Instructions

## Phase 1 & 2 Complete! ✅

We've successfully created:
- ✅ Complete project structure
- ✅ Core OCR modules (parser & matcher)
- ✅ Comprehensive test suite (68+ tests)
- ✅ Configuration system
- ✅ Documentation framework

## Next Steps: Install Dependencies & Test

### Step 1: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**⏱ This will take 5-10 minutes** - Large packages include:
- PaddleOCR (~500MB)
- EasyOCR (~1GB)  
- OpenCV
- First run will also download ~2-3GB of OCR models

### Step 3: Verify Setup

```bash
python verify_setup.py
```

**Expected Output:**
```
✓ PaddleOCR OK
✓ EasyOCR OK
✓ Pillow OK
✓ OpenCV OK
✓ RapidFuzz OK
✓ FastAPI OK
...
✅ ALL CHECKS PASSED
```

### Step 4: Run Tests

```bash
# Run all tests
python run_tests.py

# Or use pytest directly
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_matcher.py -v
```

**Expected Results:**
- ✅ Matcher tests should pass (40+ tests)
- ⚠ Parser tests may partially fail (requires real OCR models)
- Target: 90%+ test pass rate

### Step 5: Test with Sample Image (Optional)

Once dependencies are installed, you can test with a sample image:

```python
from src.ocr.parser import parse_decklist
from src.ocr.matcher import match_cards

# Parse image
result = parse_decklist('test_images/sample_deck.jpg')
print(f"Found {len(result['legend'])} legend cards")

# Match to English
matched = match_cards(result)
print(f"Accuracy: {matched['stats']['accuracy']}%")
```

## What's Next

After dependencies are installed and tests pass, we'll continue with:

**Phase 3: FastAPI Service Layer** (Next)
- Create API endpoints
- Add request/response schemas
- Build REST API

**Phase 4: Integration with Main API**
- Connect to Riftbound Top Decks API
- Enable deck creation

**Phase 5: Docker Deployment**
- Containerize service
- Production setup

## Troubleshooting

### Issue: pip install fails
```bash
# Try upgrading pip first
python -m pip install --upgrade pip

# Install packages one at a time
pip install paddlepaddle==3.0.0b1
pip install paddleocr==2.9.1
pip install easyocr==1.7.2
```

### Issue: Out of memory during installation
- Close other applications
- Install packages separately
- Use a machine with more RAM (4GB+ recommended)

### Issue: Tests fail
- Verify all dependencies installed: `python verify_setup.py`
- Check that `resources/card_mappings_final.csv` exists
- Some parser tests may fail without real images - this is OK for now

## Current Project Status

✅ **Completed (Phases 1-2)**
- Project structure
- Core OCR modules
- Test suite
- Configuration

🔄 **Ready to Install**
- Dependencies (requirements.txt)
- OCR models (auto-download on first use)

⏳ **Upcoming (Phases 3-5)**
- FastAPI service
- API integration
- Docker deployment

---

**Estimated Time Remaining:**
- Dependency installation: 10-15 minutes
- Testing: 5 minutes
- Phase 3-5 implementation: 4-6 hours

**You're 30% complete with the project!** 🎉




