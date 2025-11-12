"""
Pytest Configuration and Fixtures
Shared test fixtures and configuration for all tests
"""

import pytest
import os
import tempfile
from PIL import Image
import numpy as np


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_card_mapping_csv(temp_dir):
    """Create a sample card mapping CSV for testing"""
    csv_content = """name_cn,name_en,card_number,type_en,domain_en,cost,rarity_en,image_url_en
易, 锋芒毕现,Master Yi\\, The Wuju Bladesman,01IO060,Legend,Ionia,0,Champion,https://example.com/yi.jpg
无极剑圣,Master Yi\\, The Wuju Bladesman,01IO060,Legend,Ionia,0,Champion,https://example.com/yi.jpg
小小守护者,Tiny Protector,01IO001,Unit,Ionia,1,Common,https://example.com/tiny.jpg
决斗架势,Dueling Stance,01IO002,Spell,Ionia,2,Rare,https://example.com/duel.jpg
奇亚娜, 元素女王,Qiyana\\, Empress of the Elements,01IX001,Legend,Ixtal,0,Champion,https://example.com/qiyana.jpg
奇亚娜,Qiyana\\, Empress of the Elements,01IX001,Legend,Ixtal,0,Champion,https://example.com/qiyana.jpg
疾风剑豪,Yasuo\\, The Unforgiven,01IO003,Legend,Ionia,0,Champion,https://example.com/yasuo.jpg
"""
    csv_path = os.path.join(temp_dir, "test_mappings.csv")
    with open(csv_path, 'w', encoding='utf-8-sig') as f:
        f.write(csv_content)
    return csv_path


@pytest.fixture
def sample_parsed_decklist():
    """Sample parsed decklist structure (output from parser)"""
    return {
        'metadata': {
            'placement': 92,
            'event': '第一赛季区域公开赛-杭州赛区',
            'date': '2025-09-13'
        },
        'legend': [
            {'name_cn': '无极剑圣', 'quantity': 1}
        ],
        'main_deck': [
            {'name_cn': '小小守护者', 'quantity': 3},
            {'name_cn': '决斗架势', 'quantity': 2},
            {'name_cn': '不存在的卡', 'quantity': 1}
        ],
        'battlefields': [
            {'name_cn': '奇亚娜', 'quantity': 3}
        ],
        'runes': [
            {'name_cn': '易锋芒毕现', 'quantity': 12}
        ],
        'side_deck': []
    }


@pytest.fixture
def sample_image(temp_dir):
    """Create a simple test image"""
    img = Image.new('RGB', (800, 1200), color='white')
    img_path = os.path.join(temp_dir, 'test_image.jpg')
    img.save(img_path)
    return img_path


@pytest.fixture
def mock_decklist_image(temp_dir):
    """
    Create a more realistic mock decklist image
    with text regions and card-like structure
    """
    # Create a white background image
    img = np.ones((1200, 800, 3), dtype=np.uint8) * 255
    
    # Add some dark regions to simulate cards (simplified)
    # Legend section (top)
    img[100:150, 50:750] = [200, 200, 200]
    
    # Main deck section (middle)
    for i in range(5):
        y_pos = 200 + (i * 60)
        img[y_pos:y_pos+50, 50:750] = [200, 200, 200]
    
    # Runes section (bottom)
    for i in range(3):
        y_pos = 800 + (i * 60)
        img[y_pos:y_pos+50, 50:750] = [200, 200, 200]
    
    # Convert to PIL and save
    pil_img = Image.fromarray(img)
    img_path = os.path.join(temp_dir, 'mock_decklist.jpg')
    pil_img.save(img_path)
    return img_path


@pytest.fixture
def expected_deck_structure():
    """Expected structure of a matched decklist"""
    return {
        'metadata': dict,
        'legend': list,
        'main_deck': list,
        'battlefields': list,
        'runes': list,
        'side_deck': list,
        'stats': dict
    }




