"""
Comprehensive tests for api.py - FastAPI endpoints.
"""

import sys
import json
from pathlib import Path
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trailer_generator.api import app
from trailer_generator.schemas import (
    GeneratedMovie,
    CastMember,
    TrailerBreakdown,
    TrailerScene,
    CharacterDesign,
    TechnicalSpecs,
    MovieAnalysis,
)
from trailer_generator.scene_generator import SceneGeneratorError


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_movie_data():
    """Create sample movie data for testing."""
    return {
        "title": "Test Movie",
        "tagline": "Test tagline",
        "genres": ["Sci-Fi", "Thriller"],
        "plot_summary": "A scientist discovers something amazing.",
        "director_name": "Test Director",
        "director_background": "Acclaimed director",
        "writers": ["Writer One"],
        "writer_backgrounds": "Experienced writer",
        "cast": [
            {
                "actor_name": "Actor One",
                "character_name": "Character One",
                "physical_description": "Tall person with dark hair",
                "personality_traits": ["brave", "smart"],
                "acting_style": "intense",
                "role_description": "Hero"
            }
        ],
        "runtime": "120 minutes",
        "rating": "PG-13",
        "release_year": 2024,
        "production_company": "Test Studios",
        "production_company_background": "Major studio",
        "budget": "$100M",
        "themes": ["science", "survival"],
        "visual_style": "Dark and moody",
        "target_audience": "Adults"
    }


@pytest.fixture
def sample_trailer_breakdown():
    """Create sample trailer breakdown for testing."""
    return TrailerBreakdown(
        movie_title="Test Movie",
        total_duration=30,
        character_designs=[
            CharacterDesign(
                character_name="Character_One",
                image_generation_prompt="Test prompt",
                brief_identifier="tall person",
                visual_style="realistic"
            )
        ],
        scenes=[
            TrailerScene(
                scene_number=1,
                duration_seconds=8,
                scene_type="establishing",
                start_frame_prompt="Test start",
                end_frame_prompt="Test end",
                video_prompt="Test video",
                reference_images=["Character_One"],
                characters_present=["Character One"]
            )
        ],
        technical_specs=TechnicalSpecs(
            color_grading="Dark",
            aspect_ratio="16:9",
            visual_style="Cinematic",
            sound_design_notes="Suspenseful"
        ),
        character_appearance_map={"Character One": [1]}
    )


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_endpoint(self, client):
        """Test that root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "Trailer Generator API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "healthy"
        assert "endpoints" in data
        assert "generate_trailer" in data["endpoints"]
        assert "analyze_movie" in data["endpoints"]
        assert "health" in data["endpoints"]


class TestHealthCheckEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_with_api_key(self, client):
        """Test health check when API key is configured."""
        with patch('trailer_generator.api.settings') as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_model = "test-model"
            mock_settings.default_trailer_duration = 35
            mock_settings.include_narration = True

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["openrouter_configured"] is True
            assert data["model"] == "test-model"
            assert data["default_duration"] == 35
            assert data["include_narration"] is True

    def test_health_check_without_api_key(self, client):
        """Test health check when API key is not configured."""
        with patch('trailer_generator.api.settings') as mock_settings:
            mock_settings.openrouter_api_key = ""
            mock_settings.openrouter_model = "test-model"
            mock_settings.default_trailer_duration = 35
            mock_settings.include_narration = False

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["openrouter_configured"] is False


class TestGenerateTrailerEndpoint:
    """Tests for the generate-trailer endpoint."""

    def test_generate_trailer_success(self, client, sample_movie_data, sample_trailer_breakdown):
        """Test successful trailer generation."""
        with patch('trailer_generator.api.SceneGenerator') as mock_generator_class:
            # Mock the generator
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            mock_generator.generate_trailer.return_value = sample_trailer_breakdown

            # Make request
            request_data = {
                "movie": sample_movie_data,
                "target_duration": 30,
                "include_narration": True
            }

            response = client.post("/generate-trailer", json=request_data)

            # Verify response
            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["trailer"] is not None
            assert data["trailer"]["movie_title"] == "Test Movie"
            assert data["trailer"]["total_duration"] == 30
            assert data["error"] is None
            assert "generation_time_seconds" in data

    def test_generate_trailer_with_custom_model(self, client, sample_movie_data, sample_trailer_breakdown):
        """Test trailer generation with custom model."""
        with patch('trailer_generator.api.SceneGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            mock_generator.generate_trailer.return_value = sample_trailer_breakdown

            request_data = {
                "movie": sample_movie_data,
                "target_duration": 35,
                "include_narration": False,
                "model": "custom-model"
            }

            response = client.post("/generate-trailer", json=request_data)

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["model_used"] == "custom-model"

            # Verify generator was called with correct parameters
            mock_generator.generate_trailer.assert_called_once()
            call_kwargs = mock_generator.generate_trailer.call_args[1]
            assert call_kwargs["target_duration"] == 35
            assert call_kwargs["include_narration"] is False
            assert call_kwargs["model_override"] == "custom-model"

    def test_generate_trailer_scene_generator_error(self, client, sample_movie_data):
        """Test handling of SceneGeneratorError."""
        with patch('trailer_generator.api.SceneGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            mock_generator.generate_trailer.side_effect = SceneGeneratorError("Test error")

            request_data = {
                "movie": sample_movie_data,
                "target_duration": 30
            }

            response = client.post("/generate-trailer", json=request_data)

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is False
            assert data["trailer"] is None
            assert "Test error" in data["error"]

    def test_generate_trailer_unexpected_error(self, client, sample_movie_data):
        """Test handling of unexpected errors."""
        with patch('trailer_generator.api.SceneGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            mock_generator.generate_trailer.side_effect = RuntimeError("Unexpected error")

            request_data = {
                "movie": sample_movie_data,
                "target_duration": 30
            }

            response = client.post("/generate-trailer", json=request_data)

            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_generate_trailer_invalid_duration_too_short(self, client, sample_movie_data):
        """Test validation of duration that's too short."""
        request_data = {
            "movie": sample_movie_data,
            "target_duration": 15  # Too short (min is 20)
        }

        response = client.post("/generate-trailer", json=request_data)

        # Should fail validation
        assert response.status_code == 422

    def test_generate_trailer_invalid_duration_too_long(self, client, sample_movie_data):
        """Test validation of duration that's too long."""
        request_data = {
            "movie": sample_movie_data,
            "target_duration": 70  # Too long (max is 60)
        }

        response = client.post("/generate-trailer", json=request_data)

        # Should fail validation
        assert response.status_code == 422

    def test_generate_trailer_missing_required_fields(self, client):
        """Test validation with missing required fields."""
        request_data = {
            "target_duration": 30
            # Missing "movie" field
        }

        response = client.post("/generate-trailer", json=request_data)

        assert response.status_code == 422

    def test_generate_trailer_invalid_movie_data(self, client):
        """Test validation with invalid movie data."""
        request_data = {
            "movie": {
                "title": "Test Movie"
                # Missing many required fields
            },
            "target_duration": 30
        }

        response = client.post("/generate-trailer", json=request_data)

        assert response.status_code == 422

    def test_generate_trailer_default_values(self, client, sample_movie_data, sample_trailer_breakdown):
        """Test that default values are applied correctly."""
        with patch('trailer_generator.api.SceneGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            mock_generator.generate_trailer.return_value = sample_trailer_breakdown

            # Request with only movie (no duration or narration)
            request_data = {
                "movie": sample_movie_data
            }

            response = client.post("/generate-trailer", json=request_data)

            assert response.status_code == 200

            # Verify default values were used
            call_kwargs = mock_generator.generate_trailer.call_args[1]
            assert call_kwargs["target_duration"] == 35  # Default
            assert call_kwargs["include_narration"] is True  # Default

    @patch('trailer_generator.api.Path')
    def test_generate_trailer_saves_output(self, mock_path, client, sample_movie_data, sample_trailer_breakdown):
        """Test that trailer output is saved to file."""
        with patch('trailer_generator.api.SceneGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            mock_generator.generate_trailer.return_value = sample_trailer_breakdown

            # Mock file operations
            mock_file = Mock()
            mock_path.return_value.__truediv__.return_value = mock_file

            request_data = {
                "movie": sample_movie_data,
                "target_duration": 30
            }

            with patch('builtins.open', create=True) as mock_open:
                response = client.post("/generate-trailer", json=request_data)

                assert response.status_code == 200


class TestAnalyzeMovieEndpoint:
    """Tests for the analyze-movie endpoint."""

    def test_analyze_movie_success(self, client, sample_movie_data):
        """Test successful movie analysis."""
        with patch('trailer_generator.api.MovieAnalyzer') as mock_analyzer_class:
            # Create mock analysis
            mock_analysis = MovieAnalysis(
                main_characters=[
                    {
                        "name": "Character One",
                        "actor": "Actor One",
                        "physical_description": "Tall person",
                        "role": "Hero",
                        "traits": "brave, smart"
                    }
                ],
                key_themes=["science", "survival"],
                visual_style_summary="Dark and moody",
                tone="tense and suspenseful",
                hook_elements=["Amazing discovery", "World at stake"]
            )

            # Mock the analyzer
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze.return_value = mock_analysis

            response = client.post("/analyze-movie", json=sample_movie_data)

            assert response.status_code == 200
            data = response.json()

            assert len(data["main_characters"]) == 1
            assert data["main_characters"][0]["name"] == "Character One"
            assert len(data["key_themes"]) == 2
            assert "science" in data["key_themes"]
            assert data["visual_style_summary"] == "Dark and moody"
            assert data["tone"] == "tense and suspenseful"

    def test_analyze_movie_invalid_data(self, client):
        """Test analysis with invalid movie data."""
        invalid_data = {
            "title": "Test Movie"
            # Missing many required fields
        }

        response = client.post("/analyze-movie", json=invalid_data)

        assert response.status_code == 422

    def test_analyze_movie_analysis_error(self, client, sample_movie_data):
        """Test handling of analysis errors."""
        with patch('trailer_generator.api.MovieAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze.side_effect = Exception("Analysis failed")

            response = client.post("/analyze-movie", json=sample_movie_data)

            assert response.status_code == 500
            assert "Failed to analyze movie" in response.json()["detail"]

    def test_analyze_movie_empty_cast(self, client, sample_movie_data):
        """Test analysis with movie that has no cast."""
        movie_data = sample_movie_data.copy()
        movie_data["cast"] = []

        with patch('trailer_generator.api.MovieAnalyzer') as mock_analyzer_class:
            mock_analysis = MovieAnalysis(
                main_characters=[],
                key_themes=["science"],
                visual_style_summary="Dark",
                tone="suspenseful",
                hook_elements=["Test hook"]
            )

            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze.return_value = mock_analysis

            response = client.post("/analyze-movie", json=movie_data)

            assert response.status_code == 200
            data = response.json()
            assert len(data["main_characters"]) == 0


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_headers_on_options(self, client):
        """Test that CORS headers are present on requests."""
        # Test with a regular GET request since OPTIONS may not be explicitly handled
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})

        # CORS headers should be present
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestLifespanEvents:
    """Tests for lifespan startup/shutdown events."""

    def test_app_starts_successfully(self):
        """Test that the app can start without errors."""
        # Creating a TestClient triggers lifespan events
        with TestClient(app) as test_client:
            # If we get here without errors, startup was successful
            response = test_client.get("/health")
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
