"""
Detect and crop metadata section using color detection

Usage:
    python detect_metadata_boundary.py "image.jpg" --crop
    python detect_metadata_boundary.py "image.jpg" --crop --output metadata_crop.png
"""
import sys
import argparse
from PIL import Image
import numpy as np

# Metadata extraction colors
METADATA_BG_COLOR_HEX = '#1e3044'
MAIN_DECK_BG_COLOR_HEX = '#013950'


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def color_distance(c1, c2):
    """Euclidean distance between two RGB colors"""
    return sum((int(a) - int(b)) ** 2 for a, b in zip(c1, c2)) ** 0.5


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Detect metadata section boundary using color detection'
    )
    parser.add_argument('image', help='Path to decklist image')
    parser.add_argument('--crop', action='store_true', help='Crop and save metadata section')
    parser.add_argument('--output', default='metadata_section_auto_crop.png', help='Output filename')
    parser.add_argument('--skip-top', type=int, default=10, help='Skip top X percent (default: 10)')
    parser.add_argument('--sample-x', type=int, default=5, help='Sample at X percent from left (default: 5)')
    
    args = parser.parse_args()
    
    try:
        img = Image.open(args.image)
        print(f"Image size: {img.width}x{img.height}px")
        
        boundary_y = detect_metadata_boundary(
            img, 
            skip_top_percent=args.skip_top, 
            sample_x_percent=args.sample_x
        )
        
        metadata_percent = (boundary_y / img.height) * 100
        
        print(f"\n✓ Metadata boundary detected at Y={boundary_y}px ({metadata_percent:.1f}%)")
        
        if args.crop:
            metadata_section = img.crop((0, 0, img.width, boundary_y))
            metadata_section.save(args.output)
            print(f"✓ Saved metadata section to: {args.output}")
            print(f"  Metadata section size: {metadata_section.width}x{metadata_section.height}px")
            print(f"\nNext steps:")
            print(f"  1. Open interactive_metadata_region_editor.html in browser")
            print(f"  2. Load {args.output}")
            print(f"  3. Draw regions for each field")
            print(f"  4. Export as metadata_regions_config_new.json")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

