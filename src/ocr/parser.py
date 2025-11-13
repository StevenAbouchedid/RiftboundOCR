"""
FINAL Two-Stage Parser with Gap-Based Card Detection
Stage 1: Detect section regions by color (#1b4e63)
Stage 2: Detect individual cards by finding background gaps
"""
import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
import easyocr
import tempfile
import sys
import re
from typing import List, Dict, Tuple, Optional
import os
from collections import defaultdict
import json
import hashlib

# Try to import pytesseract for numeric field fallback
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("[WARNING] pytesseract not installed - numeric field fallback disabled")

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize OCR (lazy loading to avoid blocking imports)
_ocr = None
_easy_reader = None
_easy_reader_cn = None

def get_paddle_ocr():
    """Lazy load PaddleOCR"""
    global _ocr
    if _ocr is None:
        print("[OCR] Initializing PaddleOCR... This may take 20-40 seconds on first run.")
        try:
            _ocr = PaddleOCR(
                use_textline_orientation=True, 
                lang='ch',
                show_log=False  # Disable verbose logging
            )
            print("[OCR] PaddleOCR ready")
        except Exception as e:
            print(f"[OCR ERROR] Failed to initialize PaddleOCR: {e}")
            raise RuntimeError(f"Failed to initialize PaddleOCR: {e}")
    return _ocr

def get_easy_reader():
    """Lazy load EasyOCR English reader"""
    global _easy_reader
    if _easy_reader is None:
        print("[OCR] Initializing EasyOCR (English)... This may take 20-30 seconds on first run.")
        try:
            _easy_reader = easyocr.Reader(['en'], gpu=False)
            print("[OCR] EasyOCR English ready")
        except Exception as e:
            print(f"[OCR ERROR] Failed to initialize EasyOCR English: {e}")
            raise RuntimeError(f"Failed to initialize EasyOCR English reader: {e}")
    return _easy_reader

def get_easy_reader_cn():
    """Lazy load EasyOCR Chinese reader"""
    global _easy_reader_cn
    if _easy_reader_cn is None:
        print("[OCR] Initializing EasyOCR (Chinese)... This may take 30-60 seconds on first run.")
        try:
            _easy_reader_cn = easyocr.Reader(['ch_sim'], gpu=False)
            print("[OCR] EasyOCR Chinese ready")
        except Exception as e:
            print(f"[OCR ERROR] Failed to initialize EasyOCR Chinese: {e}")
            raise RuntimeError(f"Failed to initialize EasyOCR Chinese reader: {e}")
    return _easy_reader_cn


# Removed - use get_easy_reader_cn() instead


SECTION_COLOR_BGR = (99, 78, 27)  # #1b4e63
BACKGROUND_COLOR_BGR = (80, 57, 1)  # #013950

# Metadata extraction colors
METADATA_BG_COLOR_HEX = '#1e3044'
MAIN_DECK_BG_COLOR_HEX = '#013950'


# ============================================================================
# POSITION-BASED METADATA EXTRACTION (from other agent repo)
# ============================================================================

def detect_metadata_boundary(img_pil, skip_top_percent=10, sample_x_percent=5):
    """
    Automatically detect metadata section boundary using color detection
    
    Args:
        img_pil: PIL Image object
        skip_top_percent: Skip top X% (to avoid status bar)
        sample_x_percent: Sample at X% from left edge
    
    Returns:
        boundary_y: Y coordinate where metadata section ends
    """
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def color_distance(c1, c2):
        """Euclidean distance between two RGB colors"""
        return sum((int(a) - int(b)) ** 2 for a, b in zip(c1, c2)) ** 0.5
    
    img_array = np.array(img_pil)
    height, width = img_array.shape[:2]
    
    metadata_rgb = hex_to_rgb(METADATA_BG_COLOR_HEX)
    main_rgb = hex_to_rgb(MAIN_DECK_BG_COLOR_HEX)
    
    skip_rows = int(height * (skip_top_percent / 100))
    sample_x = int(width * (sample_x_percent / 100))
    
    main_color_consecutive = 0
    required_consecutive = 5  # Need 5 consecutive main_color pixels to confirm
    
    # Scan down the left edge
    for y in range(skip_rows, height):
        pixel = img_array[y, sample_x][:3]  # Get RGB
        dist_to_main = color_distance(pixel, main_rgb)
        dist_to_metadata = color_distance(pixel, metadata_rgb)
        
        # Is this pixel closer to main deck color?
        if dist_to_main < dist_to_metadata and dist_to_main < 30:  # Threshold
            main_color_consecutive += 1
            if main_color_consecutive >= required_consecutive:
                # Found boundary! Back up to first main_color pixel
                return y - required_consecutive + 1
        else:
            main_color_consecutive = 0
    
    # Fallback to 20% if no clear boundary found
    return int(height * 0.20)


def extract_metadata_field_tesseract(image_path, field_name):
    """
    Fallback OCR for numeric fields using Tesseract with digit-only config
    
    Tesseract PSM (Page Segmentation Mode) options:
    - 6: Assume uniform block of text (default)
    - 7: Treat image as single text line
    - 8: Treat image as single word
    - 10: Treat image as single character (BEST for single digit)
    - 13: Raw line (bypass all preprocessing)
    
    Returns extracted number or None
    """
    if not TESSERACT_AVAILABLE:
        return None
    
    try:
        img = Image.open(image_path)
        
        # Preprocessing for better OCR
        img_gray = img.convert('L')  # Convert to grayscale
        enlarged = img_gray.resize(
            (img.width * 4, img.height * 4), 
            Image.LANCZOS
        )  # Upscale 4x for better recognition
        
        # Try multiple PSM modes with digits-only whitelist
        psm_modes = [
            (10, "single character"),  # Best for "1", "2", etc
            (8, "single word"),        # For "15", "32", etc
            (7, "single line"),        # Fallback
            (13, "raw line")           # Last resort
        ]
        
        for psm, desc in psm_modes:
            # CRITICAL: tessedit_char_whitelist=0123456789
            # This FORCES Tesseract to only output digits!
            custom_config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789'
            result = pytesseract.image_to_string(enlarged, config=custom_config).strip()
            
            if result and result.isdigit():
                return result
        
        # Fallback: Try without whitelist to see what Tesseract sees
        result = pytesseract.image_to_string(enlarged, config='--oem 3 --psm 10').strip()
        
        # Extract any digits from result
        if result:
            digits = re.findall(r'\d+', result)
            if digits:
                return digits[0]
        
        return None
        
    except Exception as e:
        return None


def extract_metadata_position_based(image_path: str, config_path='metadata_regions_config_new.json'):
    """
    Extract metadata using position-based regions with auto boundary detection
    
    Returns dict with: player, deck_name, event, date, placement, legend_name
    """
    # Load config
    try:
        # Try config path relative to script
        if not os.path.exists(config_path):
            # Try relative to project root
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"  [Metadata] Config not found at {config_path}, using pattern-based fallback")
        return None
    
    # Load image
    img = Image.open(image_path)
    full_width, full_height = img.size
    
    # Auto-detect metadata boundary
    metadata_height = detect_metadata_boundary(img)
    metadata_section = img.crop((0, 0, full_width, metadata_height))
    
    result = {
        'player': None,
        'deck_name': None,
        'event': None,
        'date': None,
        'placement': None,
        'legend_name': None
    }
    
    # Extract each field
    for field_name in ['player', 'deck_name', 'event', 'date', 'placement']:
        if field_name not in config.get('regions', {}):
            continue
        
        region = config['regions'][field_name]
        section_width, section_height = metadata_section.size
        
        # Calculate crop using percentages
        x = int(section_width * float(region['x_percent']) / 100)
        y = int(section_height * float(region['y_percent']) / 100)
        w = int(section_width * float(region['width_percent']) / 100)
        h = int(section_height * float(region['height_percent']) / 100)
        
        # Bounds checking
        x = max(0, min(x, section_width))
        y = max(0, min(y, section_height))
        w = max(1, min(w, section_width - x))
        h = max(1, min(h, section_height - y))
        
        # Crop the specific field region
        crop = metadata_section.crop((x, y, x+w, y+h))
        temp_path = f"temp_{field_name}_crop.png"
        crop.save(temp_path)
        
        # Run PaddleOCR
        try:
            ocr_result = get_paddle_ocr().ocr(temp_path)
            texts = []
            if ocr_result:
                for page in ocr_result:
                    if hasattr(page, 'rec_texts'):
                        texts.extend(page.rec_texts or [])
                    elif isinstance(page, dict):
                        texts.extend(page.get('rec_texts', []))
                    elif isinstance(page, list):
                        for item in page:
                            if isinstance(item, list) and len(item) >= 2:
                                texts.append(item[1][0] if isinstance(item[1], tuple) else item[1])
            
            if texts:
                combined_text = ' '.join(texts).strip()
                
                # Field-specific processing and validation
                if field_name == 'placement':
                    # MUST be a number
                    match = re.search(r'\d+', combined_text)
                    if match and match.group().isdigit():
                        result[field_name] = int(match.group())
                    else:
                        # Validation failed - try Tesseract
                        fallback = extract_metadata_field_tesseract(temp_path, field_name)
                        if fallback:
                            result[field_name] = int(fallback)
                
                elif field_name == 'date':
                    # MUST match YYYY-MM-DD format
                    match = re.search(r'\d{4}-\d{2}-\d{2}', combined_text)
                    if match:
                        result[field_name] = match.group()
                
                else:
                    # For player, event, deck_name - accept as-is
                    result[field_name] = combined_text
            
            elif field_name == 'placement':
                # No text from PaddleOCR - try Tesseract directly
                fallback = extract_metadata_field_tesseract(temp_path, field_name)
                if fallback:
                    result[field_name] = int(fallback)
        
        except Exception as e:
            print(f"  [Metadata] Error extracting {field_name}: {e}")
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    return result

# ============================================================================
# END POSITION-BASED METADATA EXTRACTION
# ============================================================================

def detect_section_regions(image_path: str, tolerance=15):
    """Stage 1: Detect large section regions by color"""
    img = cv2.imread(image_path)
    if img is None:
        return []
    
    height, width = img.shape[:2]
    
    lower = np.array([max(0, c - tolerance) for c in SECTION_COLOR_BGR])
    upper = np.array([min(255, c + tolerance) for c in SECTION_COLOR_BGR])
    mask = cv2.inRange(img, lower, upper)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    sections = []
    min_area = (width * height) * 0.05
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            x, y, w, h = cv2.boundingRect(contour)
            sections.append({
                'box': (x, y, w, h),
                'area': area,
                'center_y': y + h/2
            })
    
    sections.sort(key=lambda s: s['center_y'])
    return sections

def detect_card_boxes_in_section(image_path: str, section_box: Tuple[int, int, int, int]):
    """
    Stage 2: Detect individual card boxes by finding background gaps
    """
    x, y, w, h = section_box
    
    img = cv2.imread(image_path)
    section_img = img[y:y+h, x:x+w]
    
    # Detect BACKGROUND (gaps between cards)
    tolerance = 15
    bg_lower = np.array([max(0, c - tolerance) for c in BACKGROUND_COLOR_BGR])
    bg_upper = np.array([min(255, c + tolerance) for c in BACKGROUND_COLOR_BGR])
    bg_mask = cv2.inRange(section_img, bg_lower, bg_upper)
    
    # Invert to get card regions
    card_regions = cv2.bitwise_not(bg_mask)
    
    # Clean up
    kernel = np.ones((5,5), np.uint8)
    card_regions = cv2.morphologyEx(card_regions, cv2.MORPH_CLOSE, kernel, iterations=2)
    card_regions = cv2.morphologyEx(card_regions, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Find contours
    contours, _ = cv2.findContours(card_regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter for card-sized regions
    card_boxes = []
    
    for contour in contours:
        cx, cy, cw, ch = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        aspect = cw / ch if ch > 0 else 0
        
        min_aspect = 1.8
        max_aspect = 6.0
        min_width = w * 0.30
        max_width = w * 0.52
        min_height = 35
        max_height = max(150, h * 0.15)  # At least 150px or 15% of height
        min_area = 8000
        
        if (min_aspect < aspect < max_aspect and
            min_width < cw < max_width and
            min_height < ch < max_height and
            area > min_area):
            
            abs_box = (x + cx, y + cy, cw, ch)
            card_boxes.append(abs_box)
    
    # Sort by position (top to bottom, left to right)
    card_boxes.sort(key=lambda b: (b[1], b[0]))
    
    return card_boxes

def ocr_card_box(image_path: str, box: Tuple[int, int, int, int]) -> Dict:
    """OCR a single card box with position-aware quantity detection"""
    x, y, w, h = box

    img = Image.open(image_path)
    cropped = img.crop((x, y, x + w, y + h))

    # Extract name with fallback handling
    card_name, name_texts, name_method = extract_name_with_fallback(cropped, w, h)

    # RIGHT 11%: Quantity region - starts exactly where the name region ends
    # Name covers 25%-89%; quantity starts at 89%
    split_point = int(w * 0.89)
    quantity_region = cropped.crop((split_point, 0, w, h))

    # Use EasyOCR - works perfectly without any preprocessing!
    temp_qty = tempfile.NamedTemporaryFile(suffix='_qty.png', delete=False)
    temp_qty_path = temp_qty.name
    temp_qty.close()
    quantity_region.save(temp_qty_path)

    # EasyOCR - reads x7, x5, etc. perfectly
    qty_result = get_easy_reader().readtext(temp_qty_path, detail=0)
    qty_text = ' '.join(qty_result).strip() if qty_result else ''

    os.remove(temp_qty_path)

    quantity = 1  # Default: empty = quantity 1

    # Parse quantity from EasyOCR output
    if qty_text:
        if re.search(r'[xX]?\d+', qty_text):
            qty_match = re.search(r'\d+', qty_text)
            if qty_match:
                qty_val = int(qty_match.group())
                if 1 <= qty_val <= 12:
                    quantity = qty_val

    confidence = 0.0

    return {
        'name_cn': card_name,
        'quantity': quantity,
        'confidence': confidence,
        'name_texts': name_texts,
        'name_method': name_method,
        'qty_text': qty_text
    }

def identify_section_type(section_index: int, section_area: float, all_areas: List[float], card_count: int = 0) -> str:
    """Identify section type by size and position"""
    sorted_areas = sorted(all_areas, reverse=True)
    
    if section_area == sorted_areas[0]:
        return 'legend_main'  # Largest (top)
    
    # After main deck, sections appear in order: Battlefields, Runes, Side Deck
    # Battlefields: typically 3 cards, medium area
    # Runes: typically 6-12 cards (6 unique), medium-large area  
    # Side Deck: typically 0-8 cards, smallest area
    
    # Use position (section_index) since sections are sorted by Y-coordinate
    if section_index == 2:
        return 'battlefields'  # Second section
    elif section_index == 3:
        return 'runes'  # Third section (or could be side deck if no runes)
    else:
        return 'side_deck'  # Fourth section or last

def parse_with_two_stage(image_path: str):
    """
    Complete two-stage parsing
    """
    print("="*60)
    print("TWO-STAGE PARSER - FINAL VERSION")
    print("="*60)
    
    result = {
        'player': None,
        'legend_name': None,
        'event': None,
        'date': None,
        'placement': None,
        'cards': {
            'legend': [],
            'main_deck': [],
            'battlefields': [],
            'runes': [],
            'side_deck': []
        }
    }
    
    # Extract metadata using position-based extraction
    print("\n[Stage 0] Extracting metadata...")
    
    # Try position-based extraction first
    metadata = extract_metadata_position_based(image_path)
    
    if metadata:
        # Position-based extraction successful
        print("  ✓ Using position-based extraction")
        result['player'] = metadata.get('player')
        result['placement'] = metadata.get('placement')
        result['event'] = metadata.get('event')
        result['date'] = metadata.get('date')
        if metadata.get('deck_name'):
            result['legend_name'] = metadata.get('deck_name')
    else:
        # Fallback to pattern-based extraction
        print("  ⚠ Using pattern-based fallback")
        img = Image.open(image_path)
        width, height = img.size
        
        metadata_crop = img.crop((0, 0, width, int(height * 0.2)))
        metadata_crop.save("temp_metadata.png")
        
        metadata_result = get_paddle_ocr().ocr("temp_metadata.png")
        
        if metadata_result:
            for page in metadata_result:
                texts = []
                if hasattr(page, 'rec_texts'):
                    texts = page.rec_texts or []
                elif isinstance(page, dict):
                    texts = page.get('rec_texts', [])
                
                for text in texts:
                    if '排名' in text or (re.match(r'^\d+$', text) and len(text) <= 3):
                        match = re.search(r'\d+', text)
                        if match and not result.get('placement'):
                            result['placement'] = int(match.group())
                    
                    elif re.search(r'\d{4}-\d{2}-\d{2}', text):
                        result['date'] = re.search(r'\d{4}-\d{2}-\d{2}', text).group()
                    
                    elif '区域公开赛' in text or '赛区' in text:
                        result['event'] = text
                    
                    elif text in ['卡莎', '德莱厄斯', '阿狸', '盖伦', '艾希', '索拉卡', '提莫', '亚索']:
                        if not result['legend_name']:
                            result['legend_name'] = text
    
    print(f"  Placement: {result.get('placement')}")
    print(f"  Event: {result.get('event')}")
    print(f"  Date: {result.get('date')}")
    print(f"  Player: {result.get('player')}")
    
    # Stage 1: Detect sections
    print("\n[Stage 1] Detecting section regions...")
    sections = detect_section_regions(image_path)
    print(f"  Found {len(sections)} sections")
    
    full_image = Image.open(image_path)

    # Stage 1.5: Classify sections and detect duplicates
    print("\n[Stage 1.5] Classifying sections...")
    all_areas = [s['area'] for s in sections]
    
    for i, section in enumerate(sections):
        section_type = classify_section_type(full_image, section['box'], i+1, all_areas, len(sections))
        section['type'] = section_type
        section['y'] = section['box'][1]  # Store y-coordinate for sorting
    
    # Detect and remove duplicate sections (common in long screenshots)
    dedup_result = detect_duplicate_sections(sections, full_image)
    sections = dedup_result['unique_sections']
    
    if dedup_result['duplicates']:
        print(f"\n[INFO] Removed {len(dedup_result['duplicates'])} duplicate section type(s)")
        for dup in dedup_result['duplicates']:
            print(f"   - {dup['count']}x {dup['type']} → kept first occurrence")
    else:
        print(f"\n[INFO] No duplicate sections found")
    
    print(f"  Processing {len(sections)} unique sections")

    section_counts = defaultdict(int)
    section_groups = []

    # Stage 2: Process each section
    print("\n[Stage 2] Detecting individual card boxes...")

    total_boxes = 0

    for i, section in enumerate(sections, 1):
        section_type = section['type']  # Already classified above

        print(f"\n  Section {i} ({section_type}):")

        card_boxes = detect_card_boxes_in_section(image_path, section['box'])
        print(f"    Found {len(card_boxes)} card boxes")
        total_boxes += len(card_boxes)

        cards_in_section = []

        for j, card_box in enumerate(card_boxes, 1):
            card_data = ocr_card_box(image_path, card_box)
            if card_data['name_cn']:
                # Set battlefields quantity to 1
                if section_type == 'battlefields':
                    card_data['quantity'] = 1
                card_data['section_index'] = i
                card_data['section_type'] = section_type
                cards_in_section.append(card_data)

        section_groups.append((section_type, cards_in_section))

    print(f"\n  Total card boxes across all sections: {total_boxes}")

    # Consolidate sections with heuristics to avoid duplicates
    def deduplicate_cards(cards):
        unique = {}
        ordered = []
        for card in cards:
            name = card['name_cn']
            if not name:
                continue
            if name not in unique:
                unique[name] = card
                ordered.append(card)
            else:
                # Keep max quantity to handle duplicates
                unique[name]['quantity'] = max(unique[name]['quantity'], card['quantity'])
        return ordered

    # Merge legend/main deck first
    legend_groups = [cards for stype, cards in section_groups if stype == 'legend_main']
    if legend_groups:
        primary = legend_groups[0]
        if primary:
            result['cards']['legend'].append(primary[0])
            result['cards']['legend'][0]['quantity'] = 1
            result['cards']['main_deck'].extend(primary[1:])
        # Merge any additional legend sections into main deck
        for extra in legend_groups[1:]:
            if extra:
                result['cards']['main_deck'].extend(extra)

    # Battlefields
    battlefield_cards = []
    for stype, cards in section_groups:
        if stype == 'battlefields':
            battlefield_cards.extend(cards)
    result['cards']['battlefields'] = deduplicate_cards(battlefield_cards)[:3]

    # Collect runes and side deck candidates
    rune_cards = []
    side_deck_candidates = []
    for stype, cards in section_groups:
        if stype == 'runes':
            rune_cards.extend(cards)
        elif stype == 'side_deck':
            side_deck_candidates.append(cards)

    # Any cards with "符文" in the name belong to runes
    for cards in side_deck_candidates:
        rune_like = [card for card in cards if '符文' in card['name_cn']]
        normal = [card for card in cards if '符文' not in card['name_cn']]
        if rune_like:
            rune_cards.extend(rune_like)
        if normal:
            result['cards']['side_deck'].extend(normal)

    result['cards']['runes'] = deduplicate_cards(rune_cards)
    result['cards']['side_deck'] = deduplicate_cards(result['cards']['side_deck'])

    # Any remaining sections (e.g., misclassified main deck pieces) should fall back into main deck
    already_handled_sections = {'legend_main', 'battlefields', 'runes', 'side_deck'}
    for stype, cards in section_groups:
        if stype not in already_handled_sections:
            result['cards']['main_deck'].extend(cards)

    result['cards']['main_deck'] = deduplicate_cards(result['cards']['main_deck'])

    # Cleanup (most temp files are now in system temp directory)
    for temp_file in ["temp_metadata.png"]:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    # Print results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    for section, cards in result['cards'].items():
        if cards:
            total = sum(c['quantity'] for c in cards)
            expected = {'legend': 1, 'main_deck': 40, 'battlefields': 3, 'runes': 12, 'side_deck': '0-8'}
            status = "✓" if (section == 'legend' and total == 1) or \
                           (section == 'main_deck' and total == 40) or \
                           (section == 'battlefields' and total == 3) or \
                           (section == 'runes' and total == 12) or \
                           (section == 'side_deck' and total <= 8) else "✗"
            
            print(f"\n{status} {section.upper().replace('_', ' ')}: {total} cards (expected: {expected[section]})")
            for card in cards:
                print(f"  {card['quantity']}x {card['name_cn']}")
    
    return result

def _paddle_name_ocr(region: Image.Image):
    temp_name_file = tempfile.NamedTemporaryFile(suffix='_name.png', delete=False)
    temp_name_path = temp_name_file.name
    temp_name_file.close()
    region.save(temp_name_path)

    try:
        result = get_paddle_ocr().ocr(temp_name_path)
        texts = []
        if result:
            for page in result:
                if hasattr(page, 'rec_texts'):
                    texts = page.rec_texts or []
                elif isinstance(page, dict):
                    texts = page.get('rec_texts', [])
        card_name = _extract_card_name_from_texts(texts)
        return card_name, texts
    finally:
        if os.path.exists(temp_name_path):
            os.remove(temp_name_path)


def _easyocr_cn(region: Image.Image):
    reader_cn = get_easy_reader_cn()
    result = reader_cn.readtext(np.array(region), detail=0)
    cleaned = [text.strip() for text in result if text.strip()]
    card_name = cleaned[0] if cleaned else None
    return card_name, cleaned


def _extract_card_name_from_texts(texts):
    accumulated = ''
    for text in texts:
        cleaned = text.strip()
        if cleaned in ['传奇牌', '主牌组', '战场牌', '符文牌', '备牌']:
            continue
        if re.match(r'^[xX]?\d+$', cleaned):
            continue
        cleaned = re.sub(r'\s*[xX]\d+\s*', '', cleaned).strip()
        if cleaned and not re.match(r'^[\d\sxX]+$', cleaned):
            accumulated += cleaned
            if len(accumulated) >= 2:
                return accumulated
    return accumulated or None


def extract_name_with_fallback(cropped: Image.Image, w: int, h: int):
    """Extract card name using PaddleOCR with fallbacks."""
    name_regions = [
        (cropped.crop((int(w * 0.25), 0, int(w * 0.89), h)), 'paddle_25_89'),
        (cropped.crop((int(w * 0.20), 0, int(w * 0.92), h)), 'paddle_20_92'),
        (cropped, 'paddle_full'),
    ]

    for region, label in name_regions:
        card_name, texts = _paddle_name_ocr(region)
        if card_name and len(card_name) >= 2:
            return card_name, texts, label

    # Fallback: EasyOCR Chinese
    card_name, texts = _easyocr_cn(name_regions[0][0])
    if card_name and len(card_name) >= 2:
        return card_name, texts, 'easyocr_cn'

    return None, [], 'failed'


HEADER_KEYWORDS = {
    'legend': ['传奇'],
    'main_deck': ['主牌'],
    'battlefields': ['战场'],
    'runes': ['符文'],
    'side_deck': ['备牌']
}

SECTION_LIMITS = {
    'legend_main': 1,
    'battlefields': 1,
    'runes': 1,
    'side_deck': 1
}


def compute_section_content_hash(image: Image.Image, y_start: int, y_end: int) -> str:
    """
    Compute MD5 hash of visual content to detect identical sections.
    Used for duplicate section detection in long screenshots.
    """
    try:
        section_crop = image.crop((0, y_start, image.width, min(y_end, image.height)))
        section_array = np.array(section_crop)
        return hashlib.md5(section_array.tobytes()).hexdigest()
    except Exception as e:
        print(f"[WARNING] Failed to compute section hash: {e}")
        return ""


def detect_duplicate_sections(sections: List[Dict], full_image: Image.Image) -> Dict:
    """
    Detect if any logical deck sections are duplicated (common in long screenshots).
    
    Returns dict with:
        - unique_sections: list of sections to keep (first occurrence of each type)
        - duplicates: list of detected duplicate section info
    """
    print(f"\n[Duplicate Detection] Checking {len(sections)} sections...")
    
    # Group sections by type
    by_type = {}
    for idx, section in enumerate(sections):
        stype = section['type']
        if stype not in by_type:
            by_type[stype] = []
        by_type[stype].append((idx, section))
    
    # Find duplicates
    duplicates = []
    sections_to_keep = []
    
    for stype, occurrences in by_type.items():
        if len(occurrences) > 1:
            print(f"\n[DUPLICATE] Found {len(occurrences)}x {stype} sections")
            print(f"   -> Keeping first occurrence only (long screenshot detected)")
            
            # Always keep only the first occurrence
            # Duplicates are from scrolling, not legitimate multiple sections
            duplicates.append({
                'type': stype,
                'count': len(occurrences),
                'kept_index': occurrences[0][0],
                'removed_indices': [occ[0] for occ in occurrences[1:]]
            })
            sections_to_keep.append(occurrences[0][1])
        else:
            # Only one occurrence, keep it
            sections_to_keep.append(occurrences[0][1])
    
    return {
        'unique_sections': sections_to_keep,
        'duplicates': duplicates
    }


def classify_section_type(full_image: Image.Image, section_box: Tuple[int, int, int, int], index: int,
                           all_areas: List[float], total_sections: int) -> str:
    x, y, w, h = section_box
    header_height = max(50, min(int(h * 0.2), 140))
    header_crop = full_image.crop((x + 5, y, x + w - 5, y + header_height))

    try:
        reader_cn = get_easy_reader_cn()
        header_texts = reader_cn.readtext(np.array(header_crop), detail=0)
        normalized = ''.join(header_texts) if header_texts else ''
    except Exception as e:
        print(f"[WARNING] Failed to read section header: {e}")
        normalized = ''
    if normalized:
        print(f"    [Header OCR] Section {index}: {normalized}")

    if normalized:
        if any(key in normalized for key in HEADER_KEYWORDS['legend']):
            return 'legend_main'
        if any(key in normalized for key in HEADER_KEYWORDS['battlefields']):
            return 'battlefields'
        if any(key in normalized for key in HEADER_KEYWORDS['runes']):
            return 'runes'
        if any(key in normalized for key in HEADER_KEYWORDS['side_deck']):
            return 'side_deck'
        if any(key in normalized for key in HEADER_KEYWORDS['main_deck']):
            return 'legend_main'

    # Fallback: Use area-based ordering, but side deck is almost always the LAST section
    sorted_areas = sorted(all_areas, reverse=True)
    section_area = w * h
    
    if section_area == sorted_areas[0]:
        return 'legend_main'
    elif section_area == sorted_areas[1]:
        return 'battlefields'
    elif section_area == sorted_areas[2]:
        return 'runes'
    else:
        # For remaining small sections:
        # - Only the VERY LAST section defaults to side_deck
        # - All others are likely runes (OCR failed to read "符文" header)
        if index == total_sections:  # Only the very last section
            return 'side_deck'
        else:
            return 'runes'  # All other middle sections are likely runes


if __name__ == "__main__":
    test_image = "test image.jpg"
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    
    result = parse_with_two_stage(test_image)



