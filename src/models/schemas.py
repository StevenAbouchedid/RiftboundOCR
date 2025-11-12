"""
Pydantic Schemas for API Request/Response Validation
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import date


class CardData(BaseModel):
    """Individual card data with Chinese and English information"""
    
    # OCR extracted fields
    name_cn: str = Field(..., description="Chinese card name")
    quantity: int = Field(..., ge=1, le=12, description="Card quantity (1-12)")
    
    # Matched English fields
    name_en: Optional[str] = Field(None, description="English card name")
    card_number: Optional[str] = Field(None, description="Card number (e.g., 01IO060)")
    type_en: Optional[str] = Field(None, description="Card type (Legend, Unit, Spell, etc.)")
    domain_en: Optional[str] = Field(None, description="Card domain/region")
    cost: Optional[str] = Field(None, description="Mana/energy cost")
    rarity_en: Optional[str] = Field(None, description="Rarity (Common, Rare, Legendary, etc.)")
    image_url_en: Optional[str] = Field(None, description="Card image URL")
    
    # Match metadata
    match_score: Optional[float] = Field(None, ge=0, le=100, description="Match confidence score (0-100)")
    match_type: Optional[str] = Field(None, description="Match strategy used")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name_cn": "易, 锋芒毕现",
                "name_en": "Master Yi, The Wuju Bladesman",
                "quantity": 1,
                "card_number": "01IO060",
                "type_en": "Legend",
                "domain_en": "Ionia",
                "cost": "0",
                "rarity_en": "Champion",
                "match_score": 100,
                "match_type": "exact_full"
            }
        }
    )


class DecklistMetadata(BaseModel):
    """Metadata extracted from decklist image"""
    
    placement: Optional[int] = Field(None, description="Tournament placement/rank")
    event: Optional[str] = Field(None, description="Event name")
    date: Optional[str] = Field(None, description="Event date")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "placement": 92,
                "event": "第一赛季区域公开赛-杭州赛区",
                "date": "2025-09-13"
            }
        }
    )


class DecklistStats(BaseModel):
    """OCR and matching accuracy statistics"""
    
    total_cards: int = Field(..., ge=0, description="Total cards in decklist")
    matched_cards: int = Field(..., ge=0, description="Successfully matched cards")
    accuracy: float = Field(..., ge=0, le=100, description="Match accuracy percentage")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_cards": 63,
                "matched_cards": 59,
                "accuracy": 93.65
            }
        }
    )


class DecklistResponse(BaseModel):
    """Complete decklist response with all sections"""
    
    decklist_id: Optional[str] = Field(None, description="Unique decklist identifier")
    metadata: DecklistMetadata = Field(..., description="Event and placement metadata")
    legend: List[CardData] = Field(default_factory=list, description="Legend cards (1)")
    main_deck: List[CardData] = Field(default_factory=list, description="Main deck cards (40)")
    battlefields: List[CardData] = Field(default_factory=list, description="Battlefield cards (3)")
    runes: List[CardData] = Field(default_factory=list, description="Rune cards (12)")
    side_deck: List[CardData] = Field(default_factory=list, description="Side deck cards (0-8)")
    stats: Optional[DecklistStats] = Field(None, description="Accuracy statistics")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decklist_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {
                    "placement": 1,
                    "event": "Season 1 Finals",
                    "date": "2025-11-01"
                },
                "legend": [
                    {
                        "name_cn": "无极剑圣",
                        "name_en": "Master Yi, The Wuju Bladesman",
                        "quantity": 1,
                        "card_number": "01IO060",
                        "match_score": 100
                    }
                ],
                "main_deck": [],
                "battlefields": [],
                "runes": [],
                "side_deck": [],
                "stats": {
                    "total_cards": 63,
                    "matched_cards": 59,
                    "accuracy": 93.65
                }
            }
        }
    )


class BatchProcessResponse(BaseModel):
    """Response for batch processing multiple images"""
    
    total: int = Field(..., description="Total images submitted")
    successful: int = Field(..., description="Successfully processed images")
    failed: int = Field(..., description="Failed images")
    average_accuracy: Optional[float] = Field(None, description="Average accuracy across all decklists")
    results: List[DecklistResponse] = Field(default_factory=list, description="Individual decklist results")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 5,
                "successful": 4,
                "failed": 1,
                "average_accuracy": 92.5,
                "results": []
            }
        }
    )


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    matcher_loaded: bool = Field(..., description="Whether card matcher is loaded")
    total_cards_in_db: int = Field(..., description="Total cards in mapping database")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "service": "RiftboundOCR",
                "version": "1.0.0",
                "matcher_loaded": True,
                "total_cards_in_db": 399
            }
        }
    )


class StatsResponse(BaseModel):
    """Service statistics response"""
    
    matcher: dict = Field(..., description="Matcher statistics")
    parser: dict = Field(..., description="Parser statistics")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matcher": {
                    "total_cards": 399,
                    "base_names": 350,
                    "supported_languages": ["zh-CN", "en"]
                },
                "parser": {
                    "ocr_engines": ["PaddleOCR", "EasyOCR"],
                    "supported_formats": ["JPG", "PNG"],
                    "max_file_size_mb": 10
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response"""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Processing failed",
                "detail": "Failed to load image: file not found",
                "code": "IMAGE_LOAD_ERROR"
            }
        }
    )


# ============================================================================
# Server-Sent Events (SSE) Schemas for Streaming Batch Processing
# ============================================================================

class SSEProgressEvent(BaseModel):
    """Progress event for SSE streaming"""
    
    current: int = Field(..., ge=1, description="Current image being processed")
    total: int = Field(..., ge=1, description="Total images in batch")
    filename: str = Field(..., description="Current filename being processed")
    status: str = Field(..., description="Processing status (processing, validating, etc.)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current": 3,
                "total": 10,
                "filename": "deck3.jpg",
                "status": "processing"
            }
        }
    )


class SSEResultEvent(BaseModel):
    """Result event for SSE streaming"""
    
    index: int = Field(..., ge=0, description="Index of the processed image")
    filename: str = Field(..., description="Filename of processed image")
    decklist: DecklistResponse = Field(..., description="Processed decklist data")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "index": 2,
                "filename": "deck3.jpg",
                "decklist": {
                    "decklist_id": "uuid",
                    "metadata": {},
                    "legend": [],
                    "main_deck": [],
                    "battlefields": [],
                    "runes": [],
                    "side_deck": [],
                    "stats": {"total_cards": 63, "matched_cards": 59, "accuracy": 93.65}
                }
            }
        }
    )


class SSEErrorEvent(BaseModel):
    """Error event for SSE streaming"""
    
    index: int = Field(..., ge=0, description="Index of the failed image")
    filename: str = Field(..., description="Filename that failed")
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error (validation, processing, etc.)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "index": 5,
                "filename": "deck6.jpg",
                "error": "Invalid file format",
                "error_type": "validation"
            }
        }
    )


class SSECompleteEvent(BaseModel):
    """Completion event for SSE streaming"""
    
    total: int = Field(..., ge=1, description="Total images in batch")
    successful: int = Field(..., ge=0, description="Successfully processed images")
    failed: int = Field(..., ge=0, description="Failed images")
    average_accuracy: Optional[float] = Field(None, ge=0, le=100, description="Average accuracy percentage")
    processing_time_seconds: Optional[float] = Field(None, ge=0, description="Total processing time")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 10,
                "successful": 8,
                "failed": 2,
                "average_accuracy": 93.2,
                "processing_time_seconds": 245.5
            }
        }
    )



