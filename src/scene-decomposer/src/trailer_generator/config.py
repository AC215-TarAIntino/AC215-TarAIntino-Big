"""
Configuration management for the trailer generator.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # OpenRouter Configuration
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # Generation Defaults
    default_trailer_duration: int = 35
    include_narration: bool = True

    # Optional: Temperature settings for LLM
    llm_temperature: float = 0.7
    llm_max_tokens: int = 12000


# Create global settings instance
settings = Settings()
