"""
Match Chinese card names to English using the card mapping database
"""
import csv
from rapidfuzz import fuzz, process
from typing import Dict, List, Optional
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class CardMatcher:
    def __init__(self, mapping_file='card-mapping-complete/final_data/card_mappings_final.csv'):
        """Load card mappings from CSV"""
        self.mappings = {}  # Full name -> card data
        self.base_name_mappings = {}  # Base name (no tagline) -> list of full names
        self.chinese_names = []
        
        with open(mapping_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name_cn = row['name_cn']
                card_data = {
                    'name_en': row['name_en'],
                    'card_number': row['card_number'],
                    'type_en': row['type_en'],
                    'domain_en': row['domain_en'],
                    'cost': row['cost'],
                    'rarity_en': row['rarity_en'],
                    'image_url_en': row.get('image_url_en', '')
                }
                
                # Store full name mapping
                if name_cn in self.mappings:
                    if not isinstance(self.mappings[name_cn], list):
                        self.mappings[name_cn] = [self.mappings[name_cn]]
                    self.mappings[name_cn].append(card_data)
                else:
                    self.mappings[name_cn] = card_data
                
                if name_cn not in self.chinese_names:
                    self.chinese_names.append(name_cn)
                
                # Store base name mapping (without tagline)
                base_name = name_cn.split(',')[0].strip()
                if base_name not in self.base_name_mappings:
                    self.base_name_mappings[base_name] = []
                self.base_name_mappings[base_name].append(name_cn)
        
        print(f"✓ Loaded {len(self.mappings)} card mappings")
        print(f"✓ Indexed {len(self.base_name_mappings)} base names")
    
    def match(self, chinese_name: str, threshold: int = 85) -> Optional[Dict]:
        """
        Match Chinese name to database with multiple strategies
        
        Args:
            chinese_name: Chinese card name from OCR
            threshold: Minimum similarity score for fuzzy matching (0-100)
            
        Returns:
            Dict with English card data or None
        """
        # Strategy 1: Exact full name match
        if chinese_name in self.mappings:
            exact_matches = [self.mappings[chinese_name]] if not isinstance(self.mappings[chinese_name], list) else self.mappings[chinese_name]
            
            if isinstance(exact_matches, list):
                exact_matches.sort(key=lambda x: x.get('card_number', 'ZZZ'))
                best_match = exact_matches[0]
            else:
                best_match = exact_matches
            
            return {
                **best_match,
                'name_cn': chinese_name,
                'match_score': 100,
                'match_type': 'exact_full'
            }
        
        # Strategy 2: Base name match (without tagline)
        # OCR might read "奇亚娜" when mapping has "奇亚娜, 所向披靡"
        if chinese_name in self.base_name_mappings:
            full_names = self.base_name_mappings[chinese_name]
            # If multiple variants exist, pick the one with lowest card number
            all_matches = []
            for full_name in full_names:
                matches = [self.mappings[full_name]] if not isinstance(self.mappings[full_name], list) else self.mappings[full_name]
                all_matches.extend(matches)
            
            all_matches.sort(key=lambda x: x.get('card_number', 'ZZZ'))
            best_match = all_matches[0]
            
            return {
                **best_match,
                'name_cn': chinese_name,
                'matched_to': full_names[0],
                'match_score': 100,
                'match_type': 'base_name'
            }
        
        # Strategy 3: Comma insertion for champion names read as one line
        # e.g., "易锋芒毕现" -> "易, 锋芒毕现"
        if len(chinese_name) >= 3:
            for split_pos in [1, 2, 3]:
                if split_pos < len(chinese_name):
                    comma_variant = chinese_name[:split_pos] + ', ' + chinese_name[split_pos:]
                    if comma_variant in self.mappings:
                        exact_matches = [self.mappings[comma_variant]] if not isinstance(self.mappings[comma_variant], list) else self.mappings[comma_variant]
                        
                        if isinstance(exact_matches, list):
                            exact_matches.sort(key=lambda x: x.get('card_number', 'ZZZ'))
                            best_match = exact_matches[0]
                        else:
                            best_match = exact_matches
                        
                        return {
                            **best_match,
                            'name_cn': chinese_name,
                            'matched_to': comma_variant,
                            'match_score': 100,
                            'match_type': 'comma_inserted'
                        }
        
        # Strategy 4: Fuzzy match on base names (more lenient for OCR errors)
        # Try to match against base names with high threshold
        base_names_list = list(self.base_name_mappings.keys())
        result = process.extractOne(
            chinese_name,
            base_names_list,
            scorer=fuzz.ratio,
            score_cutoff=threshold
        )
        
        if result:
            matched_base_name, score, _ = result
            full_names = self.base_name_mappings[matched_base_name]
            
            # Get card data for first variant
            all_matches = []
            for full_name in full_names:
                matches = [self.mappings[full_name]] if not isinstance(self.mappings[full_name], list) else self.mappings[full_name]
                all_matches.extend(matches)
            
            all_matches.sort(key=lambda x: x.get('card_number', 'ZZZ'))
            best_match = all_matches[0]
            
            return {
                **best_match,
                'name_cn': chinese_name,
                'matched_to': full_names[0],
                'match_score': score,
                'match_type': 'fuzzy_base_name'
            }
        
        # Strategy 5: Fuzzy match on full names (last resort)
        result = process.extractOne(
            chinese_name,
            self.chinese_names,
            scorer=fuzz.ratio,
            score_cutoff=threshold
        )
        
        if result:
            matched_name, score, _ = result
            matches = [self.mappings[matched_name]] if not isinstance(self.mappings[matched_name], list) else self.mappings[matched_name]
            
            if isinstance(matches, list):
                matches.sort(key=lambda x: x.get('card_number', 'ZZZ'))
                best_match = matches[0]
            else:
                best_match = matches
            
            return {
                **best_match,
                'name_cn': chinese_name,
                'matched_to': matched_name,
                'match_score': score,
                'match_type': 'fuzzy_full'
            }
        
        return None
    
    def match_decklist(self, parsed_decklist: Dict) -> Dict:
        """
        Match all cards in a parsed decklist
        
        Returns:
            Dict with matched cards and metadata (flattened structure for API response)
        """
        # Initialize with flattened structure (cards at top level, not nested)
        matched = {
            'metadata': {
                'player': parsed_decklist.get('player'),
                'legend_name': parsed_decklist.get('legend_name'),
                'event': parsed_decklist.get('event'),
                'date': parsed_decklist.get('date'),
                'placement': parsed_decklist.get('placement')
            },
            'legend': [],
            'main_deck': [],
            'battlefields': [],
            'runes': [],
            'side_deck': [],
            'unmatched': []
        }
        
        # Match legend name if provided
        if parsed_decklist.get('legend_name'):
            legend_match = self.match(parsed_decklist['legend_name'])
            if legend_match:
                matched['metadata']['legend_name_en'] = legend_match['name_en']
        
        # Match cards in each section
        for section, cards in parsed_decklist['cards'].items():
            for card in cards:
                match_result = self.match(card['name_cn'])
                
                if match_result:
                    # Image URL is already in match_result
                    image_url_en = match_result.get('image_url_en', '')
                    
                    # Add to the flattened section (not nested under 'cards')
                    matched[section].append({
                        'name_cn': card['name_cn'],
                        'name_en': match_result['name_en'],
                        'card_number': match_result['card_number'],
                        'type_en': match_result['type_en'],
                        'quantity': card['quantity'],
                        'match_score': match_result['match_score'],
                        'match_type': match_result['match_type'],
                        'ocr_confidence': card['confidence'],
                        'image_url_en': image_url_en
                    })
                else:
                    matched['unmatched'].append({
                        'name_cn': card['name_cn'],
                        'section': section,
                        'quantity': card['quantity']
                    })
        
        # Calculate stats
        total_cards = sum(len(matched[section]) for section in ['legend', 'main_deck', 'battlefields', 'runes', 'side_deck'])
        matched_cards = total_cards  # All cards in the sections are matched
        unmatched_count = len(matched['unmatched'])
        total_with_unmatched = total_cards + unmatched_count
        
        matched['stats'] = {
            'total_cards': total_with_unmatched,
            'matched_cards': matched_cards,
            'accuracy': (matched_cards / total_with_unmatched * 100) if total_with_unmatched > 0 else 0.0
        }
        
        return matched
    
    def print_matched_decklist(self, matched: Dict):
        """Pretty print matched decklist"""
        print("\n" + "="*60)
        print("MATCHED DECKLIST (Chinese → English)")
        print("="*60)
        
        meta = matched['metadata']
        if meta.get('player'):
            print(f"Player: {meta['player']}")
        if meta.get('placement'):
            print(f"Placement: {meta['placement']}")
        if meta.get('legend_name_en'):
            print(f"Legend: {meta.get('legend_name')} → {meta['legend_name_en']}")
        if meta.get('event'):
            print(f"Event: {meta['event']}")
        if meta.get('date'):
            print(f"Date: {meta['date']}")
        
        # Iterate through card sections (now at top level, not nested under 'cards')
        for section in ['legend', 'main_deck', 'battlefields', 'runes', 'side_deck']:
            cards = matched.get(section, [])
            if cards:
                print(f"\n{section.upper().replace('_', ' ')}:")
                print("-" * 60)
                for card in cards:
                    match_indicator = "✓" if card['match_score'] == 100 else "~"
                    print(f"  {match_indicator} {card['quantity']}x {card['name_cn']} → {card['name_en']}")
                    if card['match_score'] < 100:
                        print(f"      (fuzzy match: {card['match_score']:.0f}%)")
                total = sum(c['quantity'] for c in cards)
                print(f"  Total: {total} cards")
        
        if matched.get('unmatched'):
            print(f"\n⚠️  UNMATCHED CARDS:")
            print("-" * 60)
            for card in matched['unmatched']:
                print(f"  {card['quantity']}x {card['name_cn']} (section: {card['section']})")
        
        # Print stats if available
        if matched.get('stats'):
            stats = matched['stats']
            print(f"\n📊 STATS:")
            print("-" * 60)
            print(f"  Total Cards: {stats['total_cards']}")
            print(f"  Matched: {stats['matched_cards']}")
            print(f"  Accuracy: {stats['accuracy']:.2f}%")
        
        print("\n" + "="*60)



