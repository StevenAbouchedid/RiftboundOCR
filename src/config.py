"""
Configuration Management
Loads settings from environment variables
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Service Configuration
    service_host: str = "0.0.0.0"
    # Railway uses PORT, we use SERVICE_PORT - check both
    service_port: int = int(os.getenv("PORT") or os.getenv("SERVICE_PORT") or "8002")
    debug: bool = False
    
    # OCR Settings
    use_gpu: bool = False
    enable_logging: bool = True
    
    # Main API Integration (Riftbound Top Decks API)
    main_api_url: str = "http://localhost:8000/api"
    main_api_key: Optional[str] = None
    
    # File Upload Limits
    max_file_size_mb: int = 10
    max_batch_size: int = 10
    
    # Parallel Processing Settings (Phase 9)
    enable_parallel: bool = False  # Enable parallel batch processing
    max_workers: int = 2  # Number of parallel workers (2-4 recommended for CPU, 1-2 for GPU)
    
    # Model Cache Paths
    paddleocr_model_path: str = "/root/.paddlex"
    easyocr_model_path: str = "/root/.EasyOCR"
    
    # Card Mapping Path
    card_mapping_path: str = "resources/card_mappings_final.csv"
    
    # Application Info
    app_name: str = "RiftboundOCR Service"
    app_version: str = "1.0.0"
    app_description: str = "Convert Chinese decklist screenshots to structured deck data"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

