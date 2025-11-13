"""
Unit Tests for Card Matcher Module
Tests Chinese → English card matching with multiple strategies
"""

import pytest
from src.ocr.matcher import CardMatcher, match_cards


class TestCardMatcherInitialization:
    """Test matcher initialization and data loading"""
    
    def test_matcher_loads_csv(self, sample_card_mapping_csv):
        """Test that matcher loads mapping CSV correctly"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        assert len(matcher.mappings) > 0, "Should load card mappings"
        assert len(matcher.base_name_mappings) > 0, "Should index base names"
        assert len(matcher.chinese_names) > 0, "Should have Chinese names list"
    
    def test_matcher_loads_all_cards(self, sample_card_mapping_csv):
        """Test that all cards from CSV are loaded"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        # We have 7 rows in sample CSV, but some share base names
        assert len(matcher.chinese_names) >= 5
    
    def test_matcher_raises_error_for_missing_file(self):
        """Test that matcher raises error for non-existent file"""
        with pytest.raises(FileNotFoundError):
            CardMatcher('nonexistent_file.csv')


class TestMatchingStrategies:
    """Test different matching strategies"""
    
    def test_exact_full_name_match(self, sample_card_mapping_csv):
        """Test Strategy 1: Exact full name matching"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match('易, 锋芒毕现')
        
        assert result is not None
        assert result['match_type'] == 'exact_full'
        assert result['match_score'] == 100
        assert 'Yi' in result['name_en']
    
    def test_base_name_match(self, sample_card_mapping_csv):
        """Test Strategy 2: Base name matching (without tagline)"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        # Only provide base name without tagline
        result = matcher.match('奇亚娜')
        
        assert result is not None
        assert result['match_type'] == 'base_name'
        assert result['match_score'] == 100
        assert 'Qiyana' in result['name_en']
    
    def test_comma_insertion_match(self, sample_card_mapping_csv):
        """Test Strategy 3: Comma insertion for OCR errors"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        # OCR read as one line: "易锋芒毕现" should match "易, 锋芒毕现"
        result = matcher.match('易锋芒毕现')
        
        assert result is not None
        assert result['match_type'] == 'comma_inserted'
        assert result['match_score'] == 95
        assert 'Yi' in result['name_en']
    
    def test_fuzzy_base_name_match(self, sample_card_mapping_csv):
        """Test Strategy 4: Fuzzy matching on base names"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        # Slight OCR error in base name
        result = matcher.match('奇亞娜')  # Using variant character
        
        assert result is not None
        assert result['match_type'] in ['fuzzy_base', 'base_name']
        assert result['match_score'] >= 85
    
    def test_fuzzy_full_name_match(self, sample_card_mapping_csv):
        """Test Strategy 5: Fuzzy matching on full names"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        # OCR error: "决斗架势" vs "快斗架势"
        result = matcher.match('快斗架势', threshold=75)
        
        # Should match with fuzzy matching
        assert result is not None
        assert result['match_score'] >= 75
    
    def test_no_match_returns_none(self, sample_card_mapping_csv):
        """Test that invalid names return None"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match('完全不存在的卡牌名字')
        
        assert result is None


class TestMatchQuality:
    """Test match quality and confidence scores"""
    
    def test_exact_match_has_perfect_score(self, sample_card_mapping_csv):
        """Test that exact matches have 100% confidence"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match('无极剑圣')
        
        assert result['match_score'] == 100
    
    def test_fuzzy_match_has_lower_score(self, sample_card_mapping_csv):
        """Test that fuzzy matches have lower confidence"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match('疾凤剑豪', threshold=70)  # OCR error in "风"
        
        if result:  # May or may not match depending on threshold
            assert result['match_score'] < 100
    
    def test_threshold_filters_low_quality_matches(self, sample_card_mapping_csv):
        """Test that threshold filters out poor matches"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        # Very poor match should return None with high threshold
        result = matcher.match('随机文字', threshold=90)
        
        assert result is None


class TestDecklistMatching:
    """Test matching complete decklists"""
    
    def test_match_decklist_structure(self, sample_card_mapping_csv, sample_parsed_decklist):
        """Test that match_decklist returns correct structure"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match_decklist(sample_parsed_decklist)
        
        # Verify structure
        assert 'metadata' in result
        assert 'legend' in result
        assert 'main_deck' in result
        assert 'battlefields' in result
        assert 'runes' in result
        assert 'side_deck' in result
        assert 'stats' in result
    
    def test_match_decklist_adds_english_names(self, sample_card_mapping_csv, sample_parsed_decklist):
        """Test that English names are added to matched cards"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match_decklist(sample_parsed_decklist)
        
        # Check that legend card has English name
        assert len(result['legend']) > 0
        assert 'name_en' in result['legend'][0]
        assert result['legend'][0]['name_en'] != ''
    
    def test_match_decklist_preserves_quantities(self, sample_card_mapping_csv, sample_parsed_decklist):
        """Test that card quantities are preserved"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match_decklist(sample_parsed_decklist)
        
        # Check that quantities are preserved
        for section in ['legend', 'main_deck', 'battlefields', 'runes']:
            for card in result[section]:
                assert 'quantity' in card
                assert isinstance(card['quantity'], int)
                assert card['quantity'] > 0
    
    def test_match_decklist_includes_match_metadata(self, sample_card_mapping_csv, sample_parsed_decklist):
        """Test that match metadata is included"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match_decklist(sample_parsed_decklist)
        
        # Check first matched card has match metadata
        if result['legend']:
            card = result['legend'][0]
            assert 'match_type' in card
            assert 'match_score' in card
    
    def test_match_decklist_handles_unmatched_cards(self, sample_card_mapping_csv, sample_parsed_decklist):
        """Test that unmatched cards are marked as UNKNOWN"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match_decklist(sample_parsed_decklist)
        
        # Find the unmatched card '不存在的卡'
        unmatched_cards = [
            card for card in result['main_deck'] 
            if card.get('name_cn') == '不存在的卡'
        ]
        
        assert len(unmatched_cards) > 0
        assert unmatched_cards[0]['name_en'] == 'UNKNOWN'
        assert unmatched_cards[0]['match_type'] == 'no_match'
        assert unmatched_cards[0]['match_score'] == 0


class TestAccuracyCalculation:
    """Test accuracy statistics calculation"""
    
    def test_stats_are_calculated(self, sample_card_mapping_csv, sample_parsed_decklist):
        """Test that stats are included in result"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match_decklist(sample_parsed_decklist)
        
        assert 'stats' in result
        assert 'total_cards' in result['stats']
        assert 'matched_cards' in result['stats']
        assert 'accuracy' in result['stats']
    
    def test_accuracy_percentage_is_correct(self, sample_card_mapping_csv, sample_parsed_decklist):
        """Test that accuracy percentage is calculated correctly"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match_decklist(sample_parsed_decklist)
        
        stats = result['stats']
        expected_accuracy = (stats['matched_cards'] / stats['total_cards'] * 100) if stats['total_cards'] > 0 else 0
        
        assert abs(stats['accuracy'] - expected_accuracy) < 0.01  # Allow small floating point error
    
    def test_total_cards_count_is_correct(self, sample_card_mapping_csv, sample_parsed_decklist):
        """Test that total card count is correct"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match_decklist(sample_parsed_decklist)
        
        # Manual count: 1 (legend) + 3+2+1 (main) + 3 (battlefields) + 12 (runes) = 22
        expected_total = 1 + 3 + 2 + 1 + 3 + 12
        
        assert result['stats']['total_cards'] == expected_total
    
    def test_100_percent_accuracy_with_all_matches(self, sample_card_mapping_csv):
        """Test 100% accuracy when all cards match"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        perfect_decklist = {
            'metadata': {},
            'legend': [{'name_cn': '无极剑圣', 'quantity': 1}],
            'main_deck': [{'name_cn': '小小守护者', 'quantity': 3}],
            'battlefields': [],
            'runes': [],
            'side_deck': []
        }
        
        result = matcher.match_decklist(perfect_decklist)
        
        assert result['stats']['accuracy'] == 100.0
    
    def test_zero_percent_accuracy_with_no_matches(self, sample_card_mapping_csv):
        """Test 0% accuracy when no cards match"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        no_match_decklist = {
            'metadata': {},
            'legend': [{'name_cn': '完全不存在1', 'quantity': 1}],
            'main_deck': [{'name_cn': '完全不存在2', 'quantity': 3}],
            'battlefields': [],
            'runes': [],
            'side_deck': []
        }
        
        result = matcher.match_decklist(no_match_decklist)
        
        assert result['stats']['accuracy'] == 0.0


class TestConvenienceFunction:
    """Test the convenience function"""
    
    def test_match_cards_function_works(self, sample_card_mapping_csv, sample_parsed_decklist):
        """Test that match_cards convenience function works"""
        result = match_cards(sample_parsed_decklist, sample_card_mapping_csv)
        
        assert 'stats' in result
        assert 'legend' in result
        assert result['stats']['total_cards'] > 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_decklist(self, sample_card_mapping_csv):
        """Test matching an empty decklist"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        empty_decklist = {
            'metadata': {},
            'legend': [],
            'main_deck': [],
            'battlefields': [],
            'runes': [],
            'side_deck': []
        }
        
        result = matcher.match_decklist(empty_decklist)
        
        assert result['stats']['total_cards'] == 0
        assert result['stats']['matched_cards'] == 0
    
    def test_whitespace_in_names(self, sample_card_mapping_csv):
        """Test that whitespace is handled correctly"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match('  无极剑圣  ')  # Extra whitespace
        
        assert result is not None
        assert 'Yi' in result['name_en']
    
    def test_mixed_case_matching(self, sample_card_mapping_csv):
        """Test matching with Chinese characters (no case sensitivity issue)"""
        matcher = CardMatcher(sample_card_mapping_csv)
        
        result = matcher.match('无极剑圣')
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])





