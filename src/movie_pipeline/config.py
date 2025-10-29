"""
Configuration management for the movie pipeline.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OMDb API Configuration
    omdb_api_key: str
    omdb_base_url: str = "http://www.omdbapi.com/"

    # OpenRouter Configuration
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "google/gemini-2.0-flash-exp:free"

    # Optional: Site URL and name for OpenRouter (helps with ranking)
    openrouter_site_url: Optional[str] = None
    openrouter_site_name: Optional[str] = "Movie Pipeline"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
