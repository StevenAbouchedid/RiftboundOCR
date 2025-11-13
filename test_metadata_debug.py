"""
Quick metadata extraction test
Run this to debug why metadata is not being extracted
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ocr.parser import parse_with_two_stage
import json

def test_metadata_extraction(image_path):
    """Test metadata extraction on a specific image"""
    print("="*60)
    print("METADATA EXTRACTION DEBUG TEST")
    print("="*60)
    print(f"\nTesting image: {image_path}")
    print()
    
    # Run OCR
    result = parse_with_two_stage(image_path)
    
    print("\n" + "="*60)
    print("METADATA RESULTS")
    print("="*60)
    
    metadata = {
        'player': result.get('player'),
        'legend_name': result.get('legend_name'),
        'event': result.get('event'),
        'date': result.get('date'),
        'placement': result.get('placement')
    }
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    
    # Check if any metadata was found
    has_metadata = any(v is not None for v in metadata.values())
    
    if has_metadata:
        print("\n✅ Metadata extraction WORKING")
    else:
        print("\n❌ Metadata extraction FAILED - all fields are None")
        print("\nPossible issues:")
        print("1. metadata_regions_config_new.json not found or incorrect")
        print("2. Image format/structure different from training images")
        print("3. OCR not detecting text in metadata region")
    
    print("\n" + "="*60)
    print("CARD STATS")
    print("="*60)
    cards = result.get('cards', {})
    print(f"Legend: {len(cards.get('legend', []))} cards")
    print(f"Main Deck: {len(cards.get('main_deck', []))} cards")
    print(f"Battlefields: {len(cards.get('battlefields', []))} cards")
    print(f"Runes: {len(cards.get('runes', []))} cards")
    print(f"Side Deck: {len(cards.get('side_deck', []))} cards")
    
    return result

if __name__ == "__main__":
    # Test with a sample image
    test_image = "test_images/Screenshot_20251106_021827_WeChat.jpg"
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    
    result = test_metadata_extraction(test_image)

