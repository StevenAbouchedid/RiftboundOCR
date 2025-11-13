# Resources

## Card Mappings Database

### card_mappings_final.csv

The core database mapping Chinese card names to English cards.

**Format:**
```csv
name_cn,name_en,card_number,type_en,domain_en,cost,rarity_en,image_url_en
易, 锋芒毕现,Master Yi\, The Wuju Bladesman,01IO060,Legend,Ionia,0,Champion,https://...
```

**Fields:**
- `name_cn`: Chinese card name (may include tagline after comma)
- `name_en`: English card name
- `card_number`: Unique card identifier (e.g., 01IO060)
- `type_en`: Card type (Legend, Unit, Spell, etc.)
- `domain_en`: Card domain/region (Ionia, Noxus, etc.)
- `cost`: Mana/energy cost
- `rarity_en`: Rarity (Common, Rare, Legendary, etc.)
- `image_url_en`: URL to card image

**Stats:**
- Total cards: 399
- Encoding: UTF-8 with BOM
- Size: ~150KB

**Usage:**
```python
from src.ocr.matcher import CardMatcher

matcher = CardMatcher('resources/card_mappings_final.csv')
result = matcher.match('易锋芒毕现')
print(result['name_en'])  # "Master Yi, The Wuju Bladesman"
```

## Updating the Database

When new cards are released:

1. Add rows to `card_mappings_final.csv`
2. Ensure UTF-8 encoding with BOM
3. Test with sample images
4. Restart service to reload mappings

## Backup

Keep backups of this file - it's critical for service operation.





