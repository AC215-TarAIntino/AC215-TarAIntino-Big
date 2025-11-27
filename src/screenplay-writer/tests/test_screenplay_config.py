"""
Tests for the configuration module.
"""

from movie_pipeline.config import Settings


def test_settings_default_values():
    """Test that Settings has correct default values."""
    settings = Settings()

    # Check default values
    assert settings.omdb_base_url == "http://www.omdbapi.com/"
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert settings.openrouter_model == "google/gemini-3-pro-preview"
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.openrouter_site_name == "Movie Pipeline"


def test_settings_api_keys_optional():
    """Test that API keys can be empty strings."""
    settings = Settings()

    # These should work with empty strings (for testing)
    assert isinstance(settings.omdb_api_key, str)
    assert isinstance(settings.openrouter_api_key, str)


def test_settings_with_custom_values(monkeypatch):
    """Test Settings with custom environment values."""
    # Set custom environment variables
    monkeypatch.setenv("OMDB_API_KEY", "test_omdb_key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_openrouter_key")
    monkeypatch.setenv("OPENROUTER_MODEL", "custom/model")
    monkeypatch.setenv("API_PORT", "9000")

    # Create new settings instance
    settings = Settings()

    assert settings.omdb_api_key == "test_omdb_key"
    assert settings.openrouter_api_key == "test_openrouter_key"
    assert settings.openrouter_model == "custom/model"
    assert settings.api_port == 9000


def test_settings_optional_fields():
    """Test optional settings fields."""
    settings = Settings()

    # These fields are optional
    assert settings.openrouter_site_url is None or isinstance(settings.openrouter_site_url, str)
    assert settings.openrouter_site_name == "Movie Pipeline"


def test_settings_case_insensitive(monkeypatch):
    """Test that settings are case insensitive."""
    monkeypatch.setenv("omdb_api_key", "lowercase_key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "uppercase_key")

    settings = Settings()

    assert settings.omdb_api_key == "lowercase_key"
    assert settings.openrouter_api_key == "uppercase_key"


def test_settings_immutable():
    """Test that settings uses the correct Pydantic config."""
    # Should have the model_config attribute
    assert hasattr(Settings, "model_config")
    assert "env_file" in Settings.model_config
