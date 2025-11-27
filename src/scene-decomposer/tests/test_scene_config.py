"""
Comprehensive tests for configuration management.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trailer_generator.config import Settings, settings


class TestSettings:
    """Tests for the Settings class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        test_settings = Settings()

        # OpenRouter defaults
        assert test_settings.openrouter_model == "anthropic/claude-3.5-sonnet"
        assert test_settings.openrouter_base_url == "https://openrouter.ai/api/v1"

        # API defaults
        assert test_settings.api_host == "0.0.0.0"
        assert test_settings.api_port == 8001

        # Generation defaults
        assert test_settings.default_trailer_duration == 35
        assert test_settings.include_narration is True

        # LLM defaults
        assert test_settings.llm_temperature == 0.7
        assert test_settings.llm_max_tokens == 12000

    def test_settings_with_environment_variables(self):
        """Test that settings can be loaded from environment variables."""
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_API_KEY": "test-api-key-123",
                "OPENROUTER_MODEL": "google/gemini-2.0-flash",
                "API_PORT": "9000",
                "DEFAULT_TRAILER_DURATION": "45",
                "INCLUDE_NARRATION": "false",
                "LLM_TEMPERATURE": "0.5",
                "LLM_MAX_TOKENS": "8000",
            },
        ):
            test_settings = Settings()

            assert test_settings.api_port == 9000
            assert test_settings.default_trailer_duration == 45
            assert test_settings.include_narration is False
            assert test_settings.llm_temperature == 0.5
            assert test_settings.llm_max_tokens == 8000

    def test_extra_env_vars_ignored(self):
        """Test that extra environment variables are ignored."""
        with patch.dict(
            os.environ,
            {
                "SOME_RANDOM_VAR": "should-be-ignored",
                "ANOTHER_RANDOM_VAR": "also-ignored",
            },
        ):
            # Should not raise an error
            test_settings = Settings()
            assert not hasattr(test_settings, "some_random_var")
            assert not hasattr(test_settings, "another_random_var")

    def test_global_settings_instance(self):
        """Test that the global settings instance exists."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_openrouter_base_url_customization(self):
        """Test that OpenRouter base URL can be customized."""
        with patch.dict(
            os.environ, {"OPENROUTER_BASE_URL": "https://custom-openrouter.example.com/v1"}
        ):
            test_settings = Settings()
            assert test_settings.openrouter_base_url == "https://custom-openrouter.example.com/v1"

    def test_api_host_customization(self):
        """Test that API host can be customized."""
        with patch.dict(os.environ, {"API_HOST": "localhost"}):
            test_settings = Settings()
            assert test_settings.api_host == "localhost"

    def test_numeric_type_conversion(self):
        """Test that numeric values are properly converted from strings."""
        with patch.dict(
            os.environ,
            {
                "API_PORT": "8080",
                "DEFAULT_TRAILER_DURATION": "30",
                "LLM_TEMPERATURE": "0.9",
                "LLM_MAX_TOKENS": "15000",
            },
        ):
            test_settings = Settings()

            # Check types
            assert isinstance(test_settings.api_port, int)
            assert isinstance(test_settings.default_trailer_duration, int)
            assert isinstance(test_settings.llm_temperature, float)
            assert isinstance(test_settings.llm_max_tokens, int)

            # Check values
            assert test_settings.api_port == 8080
            assert test_settings.default_trailer_duration == 30
            assert test_settings.llm_temperature == 0.9
            assert test_settings.llm_max_tokens == 15000

    def test_boolean_type_conversion(self):
        """Test that boolean values are properly converted from strings."""
        # Test various boolean representations
        for true_value in ["true", "True", "TRUE", "1", "yes", "Yes"]:
            with patch.dict(os.environ, {"INCLUDE_NARRATION": true_value}):
                test_settings = Settings()
                assert test_settings.include_narration is True

        for false_value in ["false", "False", "FALSE", "0", "no", "No"]:
            with patch.dict(os.environ, {"INCLUDE_NARRATION": false_value}):
                test_settings = Settings()
                assert test_settings.include_narration is False

    def test_settings_immutability_after_creation(self):
        """Test that settings can be modified after creation (not frozen)."""
        test_settings = Settings()

        # Pydantic models are not frozen by default
        test_settings.api_port = 9999
        assert test_settings.api_port == 9999

    def test_model_config_attributes(self):
        """Test that model configuration is set correctly."""
        assert Settings.model_config["env_file"] == ".env"
        assert Settings.model_config["env_file_encoding"] == "utf-8"
        assert Settings.model_config["case_sensitive"] is False
        assert Settings.model_config["extra"] == "ignore"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
