"""Configuration module for Coinbase crypto pipeline.

This module handles all configuration management using environment variables
with sensible defaults for local development and production.
"""

import os
from typing import List
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # API Configuration
    COINBASE_API_BASE_URL: str = "https://api.exchange.coinbase.com"
    API_TIMEOUT: int = 30
    API_RETRIES: int = 3
    API_RETRY_DELAY: float = 1.0

    # Database Configuration
    DATABASE_URL: str = "sqlite:///coinbase_data.db"
    DB_ECHO: bool = False  # Set to True to log SQL statements

    # Data Collection Configuration
    CRYPTO_PAIRS: List[str] = ["BTC-USD", "ETH-USD", "SOL-USD"]
    FETCH_INTERVAL: int = 60  # seconds between fetches

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/crypto_pipeline.log"

    # Cache Configuration
    CACHE_TTL: int = 300  # seconds
    ENABLE_CACHE: bool = True

    # Analytics Configuration
    TECHNICAL_INDICATORS: List[str] = ["SMA_20", "SMA_50", "RSI_14"]
    ANOMALY_DETECTION_ENABLED: bool = True
    ANOMALY_THRESHOLD: float = 2.5  # standard deviations

    # Environment
    ENV: str = "development"
    DEBUG: bool = False

    @field_validator("LOG_FILE", mode="before")
    @classmethod
    def ensure_log_directory(cls, v: str) -> str:
        """Ensure log directory exists."""
        log_dir = os.path.dirname(v)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        return v

    @field_validator("CRYPTO_PAIRS", mode="before")
    @classmethod
    def parse_crypto_pairs(cls, v):
        """Allow CSV env values for CRYPTO_PAIRS."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("TECHNICAL_INDICATORS", mode="before")
    @classmethod
    def parse_technical_indicators(cls, v):
        """Allow CSV env values for TECHNICAL_INDICATORS."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Load settings
settings = Settings()

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Construct database path
DB_FILE = PROJECT_ROOT / "coinbase_data.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

__all__ = ["settings", "PROJECT_ROOT", "DATA_DIR", "DB_FILE", "DATABASE_URL"]


