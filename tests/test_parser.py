"""
Unit Tests for Decklist Parser Module
Tests image processing and OCR extraction
"""

import pytest
import numpy as np
from PIL import Image
from src.ocr.parser import DecklistParser, parse_decklist


class TestParserInitialization:
    """Test parser initialization"""
    
    def test_parser_initializes_without_gpu(self):
        """Test that parser initializes correctly without GPU"""
        parser = DecklistParser(use_gpu=False)
        
        assert parser is not None
        assert parser.ocr_ch is not None
        assert not parser._use_gpu
    
    def test_parser_lazy_loads_easyocr(self):
        """Test that EasyOCR readers are lazy-loaded"""
        parser = DecklistParser(use_gpu=False)
        
        # Should not be initialized yet
        assert parser._easyocr_en is None
        assert parser._easyocr_cn is None
        
        # Access triggers initialization
        _ = parser.easyocr_en
        assert parser._easyocr_en is not None


class TestImageLoading:
    """Test image loading and validation"""
    
    def test_parse_raises_error_for_missing_image(self):
        """Test that parse raises error for non-existent image"""
        parser = DecklistParser(use_gpu=False)
        
        with pytest.raises(ValueError, match="Failed to load image"):
            parser.parse('nonexistent_image.jpg')
    
    def test_parse_accepts_valid_image(self, sample_image):
        """Test that parse accepts valid image file"""
        parser = DecklistParser(use_gpu=False)
        
        # Should not raise error (may fail at OCR stage, but loads image)
        try:
            result = parser.parse(sample_image)
            # If it succeeds, check structure
            assert isinstance(result, dict)
        except Exception as e:
            # OCR might fail on blank image, but image should load
            assert "Failed to load image" not in str(e)


class TestOutputStructure:
    """Test output data structure"""
    
    def test_parse_returns_dict(self, sample_image):
        """Test that parse returns a dictionary"""
        parser = DecklistParser(use_gpu=False)
        
        result = parser.parse(sample_image)
        
        assert isinstance(result, dict)
    
    def test_parse_includes_all_sections(self, sample_image):
        """Test that result includes all required sections"""
        parser = DecklistParser(use_gpu=False)
        
        result = parser.parse(sample_image)
        
        # Check required sections
        assert 'metadata' in result
        assert 'legend' in result
        assert 'main_deck' in result
        assert 'battlefields' in result
        assert 'runes' in result
        assert 'side_deck' in result
    
    def test_metadata_has_expected_fields(self, sample_image):
        """Test that metadata has expected fields"""
        parser = DecklistParser(use_gpu=False)
        
        result = parser.parse(sample_image)
        metadata = result['metadata']
        
        assert 'placement' in metadata
        assert 'event' in metadata
        assert 'date' in metadata
    
    def test_sections_are_lists(self, sample_image):
        """Test that all card sections are lists"""
        parser = DecklistParser(use_gpu=False)
        
        result = parser.parse(sample_image)
        
        assert isinstance(result['legend'], list)
        assert isinstance(result['main_deck'], list)
        assert isinstance(result['battlefields'], list)
        assert isinstance(result['runes'], list)
        assert isinstance(result['side_deck'], list)


class TestCardStructure:
    """Test individual card data structure"""
    
    def test_card_has_required_fields(self, mock_decklist_image):
        """Test that extracted cards have required fields"""
        parser = DecklistParser(use_gpu=False)
        
        result = parser.parse(mock_decklist_image)
        
        # Check any extracted cards have correct structure
        all_cards = (
            result['legend'] + 
            result['main_deck'] + 
            result['battlefields'] + 
            result['runes'] + 
            result['side_deck']
        )
        
        for card in all_cards:
            assert 'name_cn' in card, "Card should have Chinese name"
            assert 'quantity' in card, "Card should have quantity"
    
    def test_card_quantities_are_integers(self, mock_decklist_image):
        """Test that quantities are integers"""
        parser = DecklistParser(use_gpu=False)
        
        result = parser.parse(mock_decklist_image)
        
        all_cards = (
            result['legend'] + 
            result['main_deck'] + 
            result['battlefields'] + 
            result['runes'] + 
            result['side_deck']
        )
        
        for card in all_cards:
            assert isinstance(card['quantity'], int)
    
    def test_card_quantities_in_valid_range(self, mock_decklist_image):
        """Test that quantities are in valid range"""
        parser = DecklistParser(use_gpu=False)
        
        result = parser.parse(mock_decklist_image)
        
        all_cards = (
            result['legend'] + 
            result['main_deck'] + 
            result['battlefields'] + 
            result['runes'] + 
            result['side_deck']
        )
        
        for card in all_cards:
            assert 1 <= card['quantity'] <= 12, f"Invalid quantity: {card['quantity']}"


class TestMetadataExtraction:
    """Test metadata extraction"""
    
    def test_extract_metadata_returns_dict(self, sample_image):
        """Test that _extract_metadata returns a dict"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(sample_image)
        metadata = parser._extract_metadata(image)
        
        assert isinstance(metadata, dict)
        assert 'placement' in metadata
        assert 'event' in metadata
        assert 'date' in metadata
    
    def test_extract_metadata_handles_errors_gracefully(self, sample_image):
        """Test that metadata extraction handles errors gracefully"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(sample_image)
        
        # Should not raise error even on blank image
        metadata = parser._extract_metadata(image)
        
        assert isinstance(metadata, dict)


class TestSectionDetection:
    """Test section boundary detection"""
    
    def test_detect_sections_returns_dict(self, sample_image):
        """Test that _detect_sections returns a dict"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(sample_image)
        sections = parser._detect_sections(image)
        
        assert isinstance(sections, dict)
    
    def test_detect_sections_includes_all_sections(self, sample_image):
        """Test that all sections are detected"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(sample_image)
        sections = parser._detect_sections(image)
        
        expected_sections = ['legend', 'main_deck', 'battlefields', 'runes', 'side_deck']
        for section_name in expected_sections:
            assert section_name in sections
    
    def test_section_bounds_are_tuples(self, sample_image):
        """Test that section bounds are (y_start, y_end) tuples"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(sample_image)
        sections = parser._detect_sections(image)
        
        for section_name, bounds in sections.items():
            assert isinstance(bounds, tuple)
            assert len(bounds) == 2
            assert bounds[0] < bounds[1]  # Start before end


class TestCardBoxDetection:
    """Test card box detection"""
    
    def test_detect_card_boxes_returns_list(self, mock_decklist_image):
        """Test that _detect_card_boxes returns a list"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(mock_decklist_image)
        section_image = image[100:500, :]
        
        card_regions = parser._detect_card_boxes(section_image)
        
        assert isinstance(card_regions, list)
    
    def test_card_regions_are_tuples(self, mock_decklist_image):
        """Test that card regions are (x, y, w, h) tuples"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(mock_decklist_image)
        section_image = image[100:500, :]
        
        card_regions = parser._detect_card_boxes(section_image)
        
        for region in card_regions:
            assert isinstance(region, tuple)
            assert len(region) == 4  # x, y, w, h
            x, y, w, h = region
            assert w > 0 and h > 0


class TestQuantityExtraction:
    """Test quantity number extraction"""
    
    def test_extract_quantity_returns_int_or_none(self, mock_decklist_image):
        """Test that _extract_quantity returns int or None"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(mock_decklist_image)
        region = image[100:150, 0:50]
        
        quantity = parser._extract_quantity(region)
        
        assert isinstance(quantity, int) or quantity is None
    
    def test_extract_quantity_defaults_to_one(self, sample_image):
        """Test that extraction defaults to 1 on failure"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(sample_image)
        # Blank region should default to 1
        region = image[0:50, 0:50]
        
        quantity = parser._extract_quantity(region)
        
        assert quantity == 1


class TestNameExtraction:
    """Test Chinese name extraction"""
    
    def test_extract_name_returns_string_or_none(self, mock_decklist_image):
        """Test that _extract_name returns string or None"""
        parser = DecklistParser(use_gpu=False)
        
        import cv2
        image = cv2.imread(mock_decklist_image)
        region = image[100:150, 100:700]
        
        name = parser._extract_name(region)
        
        assert isinstance(name, str) or name is None


class TestConvenienceFunction:
    """Test the convenience function"""
    
    def test_parse_decklist_function_works(self, sample_image):
        """Test that parse_decklist convenience function works"""
        result = parse_decklist(sample_image, use_gpu=False)
        
        assert isinstance(result, dict)
        assert 'metadata' in result
        assert 'legend' in result


class TestCountingCards:
    """Test card counting utility"""
    
    def test_count_total_cards(self, sample_image):
        """Test that _count_total_cards works correctly"""
        parser = DecklistParser(use_gpu=False)
        
        result = {
            'legend': [{'quantity': 1}],
            'main_deck': [{'quantity': 3}, {'quantity': 2}],
            'battlefields': [{'quantity': 3}],
            'runes': [{'quantity': 12}],
            'side_deck': []
        }
        
        total = parser._count_total_cards(result)
        
        assert total == 1 + 3 + 2 + 3 + 12
        assert total == 21


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_parser_handles_corrupted_image_gracefully(self, temp_dir):
        """Test that parser handles corrupted images gracefully"""
        import os
        
        # Create a fake image file with wrong content
        fake_image = os.path.join(temp_dir, 'fake.jpg')
        with open(fake_image, 'w') as f:
            f.write("This is not an image")
        
        parser = DecklistParser(use_gpu=False)
        
        with pytest.raises(ValueError):
            parser.parse(fake_image)
    
    def test_parser_handles_empty_sections(self, sample_image):
        """Test that parser handles empty sections correctly"""
        parser = DecklistParser(use_gpu=False)
        
        result = parser.parse(sample_image)
        
        # Empty sections should be empty lists, not None
        for section in ['legend', 'main_deck', 'battlefields', 'runes', 'side_deck']:
            assert isinstance(result[section], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




