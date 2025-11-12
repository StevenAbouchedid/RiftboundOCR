#!/usr/bin/env python3
"""
Accuracy Validation Script
Process all test images and generate accuracy report
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ocr.parser import DecklistParser
from src.ocr.matcher import CardMatcher


def validate_all_images(test_dir: str = "test_images"):
    """
    Process all test images and generate accuracy report
    
    Args:
        test_dir: Directory containing test images
    """
    test_path = Path(test_dir)
    
    # Find all JPG/PNG images
    image_files = list(test_path.glob("*.jpg")) + list(test_path.glob("*.png"))
    
    if not image_files:
        print(f"❌ No test images found in {test_dir}/")
        print("   Please add JPG or PNG images to test_images/ directory")
        return
    
    print("=" * 80)
    print(f"ACCURACY VALIDATION - RiftboundOCR")
    print("=" * 80)
    print(f"Test Directory: {test_dir}")
    print(f"Total Images: {len(image_files)}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Initialize OCR components
    print("Initializing OCR components...")
    try:
        parser = DecklistParser(use_gpu=False)
        matcher = CardMatcher()
        print("✓ OCR components initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize OCR components: {e}")
        return
    
    # Process each image
    results = []
    total_accuracy = 0
    successful_count = 0
    failed_count = 0
    
    for idx, img_path in enumerate(image_files, 1):
        print(f"[{idx}/{len(image_files)}] Processing: {img_path.name}")
        print("-" * 80)
        
        try:
            # Parse image
            print(f"  Stage 1: Parsing image...")
            parsed = parser.parse(str(img_path))
            
            # Count extracted cards
            total_extracted = sum(
                len(parsed.get(section, []))
                for section in ['legend', 'main_deck', 'battlefields', 'runes', 'side_deck']
            )
            print(f"  ✓ Extracted {total_extracted} card entries")
            
            # Match cards
            print(f"  Stage 2: Matching to English...")
            matched = matcher.match_decklist(parsed)
            
            # Get stats
            stats = matched.get('stats', {})
            accuracy = stats.get('accuracy', 0)
            total_cards = stats.get('total_cards', 0)
            matched_cards = stats.get('matched_cards', 0)
            
            print(f"  ✓ Matched {matched_cards}/{total_cards} cards ({accuracy:.2f}%)")
            
            # Determine status
            if accuracy >= 90:
                status = "✓ EXCELLENT"
                status_emoji = "🟢"
            elif accuracy >= 80:
                status = "⚠ GOOD"
                status_emoji = "🟡"
            else:
                status = "⚠ LOW ACCURACY"
                status_emoji = "🔴"
            
            print(f"  {status_emoji} {status}")
            
            # Store result
            result = {
                "filename": img_path.name,
                "accuracy": accuracy,
                "total_cards": total_cards,
                "matched_cards": matched_cards,
                "unmatched_cards": total_cards - matched_cards,
                "placement": parsed.get('metadata', {}).get('placement'),
                "event": parsed.get('metadata', {}).get('event'),
                "status": status,
                "legend": [card.get('name_en', 'UNKNOWN') for card in matched.get('legend', [])],
                "unmatched_names": [
                    card.get('name_cn') 
                    for section in ['legend', 'main_deck', 'battlefields', 'runes', 'side_deck']
                    for card in matched.get(section, [])
                    if card.get('name_en') == 'UNKNOWN'
                ]
            }
            results.append(result)
            
            total_accuracy += accuracy
            successful_count += 1
            
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed_count += 1
            results.append({
                "filename": img_path.name,
                "error": str(e),
                "status": "FAILED"
            })
        
        print()
    
    # Calculate summary statistics
    avg_accuracy = total_accuracy / successful_count if successful_count > 0 else 0
    passed = sum(1 for r in results if r.get('accuracy', 0) >= 85)
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Images:      {len(image_files)}")
    print(f"Successful:        {successful_count}")
    print(f"Failed:            {failed_count}")
    print(f"Passed (≥85%):     {passed}/{successful_count}")
    print(f"Average Accuracy:  {avg_accuracy:.2f}%")
    print("=" * 80)
    print()
    
    # Print detailed results
    if successful_count > 0:
        print("DETAILED RESULTS:")
        print("-" * 80)
        for result in results:
            if 'error' not in result:
                acc = result['accuracy']
                emoji = "🟢" if acc >= 90 else "🟡" if acc >= 80 else "🔴"
                print(f"{emoji} {result['filename']:40s} {acc:6.2f}% ({result['matched_cards']}/{result['total_cards']} cards)")
                if result['unmatched_cards'] > 0:
                    print(f"   Unmatched: {', '.join(result['unmatched_names'][:3])}")
                    if len(result['unmatched_names']) > 3:
                        print(f"   ... and {len(result['unmatched_names']) - 3} more")
        print()
    
    # Save results to JSON
    output_file = "validation_results.json"
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_images": len(image_files),
            "successful": successful_count,
            "failed": failed_count,
            "passed": passed,
            "average_accuracy": round(avg_accuracy, 2)
        },
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Results saved to: {output_file}")
    print()
    
    # Final assessment
    if avg_accuracy >= 90:
        print("🎉 EXCELLENT! Service is performing above target (≥90%)")
    elif avg_accuracy >= 85:
        print("✅ GOOD! Service is performing at target (≥85%)")
    elif avg_accuracy >= 75:
        print("⚠️  ACCEPTABLE but below target. Consider improving card mappings.")
    else:
        print("❌ POOR PERFORMANCE. Check OCR configuration and card mappings.")
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate OCR accuracy on test images")
    parser.add_argument(
        "--dir",
        default="test_images",
        help="Directory containing test images (default: test_images)"
    )
    
    args = parser.parse_args()
    
    try:
        validate_all_images(args.dir)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




