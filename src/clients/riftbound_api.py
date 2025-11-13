"""
API Client for Riftbound Top Decks API
Enables integration with the main backend for deck creation
"""

import httpx
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RiftboundAPIClient:
    """
    Client for communicating with Riftbound Top Decks API
    
    Handles deck creation, card lookups, and validation
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the main API (e.g., https://api.riftbound.com/api)
            api_key: Optional API key for authenticated requests
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # Create HTTP client
        headers = {}
        if api_key:
            headers['X-API-Key'] = api_key
        
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout
        )
        
        logger.info(f"RiftboundAPIClient initialized: {base_url}")
    
    def close(self):
        """Close HTTP client"""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    # Card Operations
    
    def get_card_by_name(self, name: str) -> Optional[Dict]:
        """
        Get card by name from main API
        
        Args:
            name: English card name
            
        Returns:
            Card data dict or None if not found
        """
        try:
            response = self.client.get(f"/cards/search", params={"q": name})
            response.raise_for_status()
            
            results = response.json()
            if results and len(results) > 0:
                return results[0]
            return None
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to lookup card '{name}': {e}")
            return None
    
    def get_card_by_number(self, card_number: str) -> Optional[Dict]:
        """
        Get card by card number from main API
        
        Args:
            card_number: Card number (e.g., "01IO060")
            
        Returns:
            Card data dict or None if not found
        """
        try:
            response = self.client.get(f"/cards", params={"card_number": card_number})
            response.raise_for_status()
            
            results = response.json()
            if results and len(results) > 0:
                return results[0]
            return None
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to lookup card number '{card_number}': {e}")
            return None
    
    # Deck Operations
    
    def create_deck(self, deck_data: Dict) -> Optional[Dict]:
        """
        Create deck in main API
        
        Args:
            deck_data: Deck data dict matching main API schema:
            {
                "name": str,
                "legend": str,
                "owner": str,
                "format_id": int,
                "cards": [
                    {"card_id": int, "quantity": int, "section": str},
                    ...
                ]
            }
            
        Returns:
            Created deck dict with ID, or None if failed
        """
        try:
            logger.info(f"Creating deck: {deck_data.get('name', 'Unknown')}")
            
            response = self.client.post("/decks", json=deck_data)
            response.raise_for_status()
            
            created_deck = response.json()
            logger.info(f"Deck created successfully with ID: {created_deck.get('id')}")
            
            return created_deck
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to create deck: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def get_deck(self, deck_id: int) -> Optional[Dict]:
        """
        Get deck by ID from main API
        
        Args:
            deck_id: Deck ID
            
        Returns:
            Deck data dict or None if not found
        """
        try:
            response = self.client.get(f"/decks/{deck_id}")
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get deck {deck_id}: {e}")
            return None
    
    # Format Operations
    
    def get_formats(self) -> List[Dict]:
        """
        Get available game formats
        
        Returns:
            List of format dicts
        """
        try:
            response = self.client.get("/formats")
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get formats: {e}")
            return []
    
    def get_format_by_name(self, name: str) -> Optional[Dict]:
        """
        Get format by name
        
        Args:
            name: Format name (e.g., "Origins", "Spiritforged")
            
        Returns:
            Format dict or None if not found
        """
        formats = self.get_formats()
        for fmt in formats:
            if fmt.get('name', '').lower() == name.lower():
                return fmt
        return None
    
    # Utility Methods
    
    def map_ocr_to_deck_schema(
        self, 
        ocr_result: Dict, 
        owner: str = "Unknown",
        format_id: int = 1,
        deck_name: Optional[str] = None
    ) -> Dict:
        """
        Map OCR result to main API deck schema
        
        Args:
            ocr_result: Output from matcher.match_decklist()
            owner: Deck owner/player name
            format_id: Format ID from main API
            deck_name: Optional deck name override
            
        Returns:
            Deck data dict ready for create_deck()
        """
        # Extract legend name
        legend = "Unknown"
        if ocr_result.get('legend') and len(ocr_result['legend']) > 0:
            legend_card = ocr_result['legend'][0]
            legend = legend_card.get('name_en', 'Unknown')
            # Extract just the name before comma if present
            if ',' in legend:
                legend = legend.split(',')[0].strip()
        
        # Generate deck name if not provided
        if not deck_name:
            placement = ocr_result.get('metadata', {}).get('placement')
            event = ocr_result.get('metadata', {}).get('event', 'Tournament')
            if placement:
                deck_name = f"{legend} - #{placement} {event}"
            else:
                deck_name = f"{legend} Deck"
        
        # Collect all cards (note: main API uses card_id, but we have card_number)
        # This requires looking up each card in the main API to get its ID
        # For now, we'll structure the data and note that card IDs need resolution
        
        cards_to_create = []
        
        # Process each section
        for section_name in ['legend', 'main_deck', 'battlefields', 'runes', 'side_deck']:
            cards = ocr_result.get(section_name, [])
            for card in cards:
                # Skip unmatched cards
                if card.get('name_en') == 'UNKNOWN':
                    logger.warning(f"Skipping unmatched card: {card.get('name_cn')}")
                    continue
                
                # Note: This requires card_id from main API
                # In production, we'd look up each card by card_number or name
                cards_to_create.append({
                    'card_number': card.get('card_number'),  # For lookup
                    'name_en': card.get('name_en'),  # For lookup
                    'quantity': card.get('quantity', 1),
                    'section': section_name
                })
        
        # Calculate total size
        total_size = sum(card['quantity'] for card in cards_to_create)
        
        return {
            'name': deck_name,
            'legend': legend,
            'owner': owner,
            'format_id': format_id,
            'size': total_size,
            'cards': cards_to_create,  # Note: Requires card_id resolution
            'metadata': ocr_result.get('metadata', {}),
            'stats': ocr_result.get('stats', {})
        }
    
    async def resolve_card_ids(self, cards: List[Dict]) -> List[Dict]:
        """
        Resolve card IDs from card numbers or names
        
        Args:
            cards: List of card dicts with 'card_number' or 'name_en'
            
        Returns:
            List of card dicts with 'card_id' added
        """
        resolved = []
        
        for card_data in cards:
            card_number = card_data.get('card_number')
            name_en = card_data.get('name_en')
            
            # Try lookup by card number first
            card_info = None
            if card_number:
                card_info = self.get_card_by_number(card_number)
            
            # Fallback to name lookup
            if not card_info and name_en:
                card_info = self.get_card_by_name(name_en)
            
            if card_info:
                resolved.append({
                    'card_id': card_info['id'],
                    'quantity': card_data['quantity'],
                    'section': card_data['section']
                })
            else:
                logger.warning(f"Could not resolve card: {name_en} ({card_number})")
        
        return resolved
    
    def health_check(self) -> bool:
        """
        Check if main API is accessible
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = self.client.get("/health")
            return response.status_code == 200
        except:
            return False





