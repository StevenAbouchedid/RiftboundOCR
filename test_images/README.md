# Test Images

Place your Chinese decklist screenshot images here for testing.

## Required Format

- **File type**: JPG or PNG
- **Resolution**: 1080p or higher recommended
- **Content**: Clear, well-lit screenshots of decklists
- **Naming**: Use descriptive names (e.g., `ahri_deck_1.jpg`, `yi_worlds_2025.jpg`)

## Recommended Test Set

For comprehensive testing, include:

1. **Different legends**: Ahri, Yi, Yasuo, etc.
2. **Different placements**: Top 8, Top 32, etc.
3. **Different events**: Regionals, Nationals, Online tournaments
4. **Different image quality**: High-res, medium-res, slightly blurry
5. **Edge cases**: Side decks, empty sections, special characters

## Sample Images Needed

Place at least 5-10 sample images here:
- `sample_deck_1.jpg`
- `sample_deck_2.jpg`
- `sample_deck_3.jpg`
- ... etc

## Usage

```bash
# Test single image
python -c "from src.ocr.parser import parse_decklist; print(parse_decklist('test_images/sample_deck_1.jpg'))"

# Run validation
python tests/validate_accuracy.py
```

## Notes

- Test images are gitignored by default (except sample_*.jpg)
- You can override this in .gitignore if you want to commit test images
- Respect privacy - don't commit images with personal information




