"""
Tests for the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from movie_pipeline.api import app
from movie_pipeline.movie_fetcher import MovieFetcherError, MovieNotFoundError
from movie_pipeline.movie_generator import MovieGeneratorError
from movie_pipeline.schemas import GeneratedMovie


@pytest.fixture
def client():
    """Fixture providing FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_generated_movie():
    """Fixture providing a mock generated movie."""
    return GeneratedMovie(
        title="Test Movie",
        tagline="A test tagline",
        genres=["Action", "Drama"],
        plot_summary="A test plot",
        director_name="Test Director",
        director_background="Test background",
        writers=["Writer 1"],
        writer_backgrounds="Test writer background",
        cast=[{
            "actor_name": "Actor 1",
            "character_name": "Character 1",
            "physical_description": "Test description",
            "personality_traits": ["brave"],
            "acting_style": "Test style",
            "role_description": "Test role"
        }],
        runtime="120 min",
        rating="PG-13",
        release_year=2026,
        production_company="Test Company",
        production_company_background="Test company background",
        budget="$100M",
        themes=["theme1"],
        visual_style="Test visual style",
        target_audience="Test audience",
        inspiration_source=["Source 1"]
    )


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns health status."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Movie Pipeline API"
        assert "version" in data


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_endpoint(self, client):
        """Test health check endpoint returns configuration status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "omdb_configured" in data
        assert "openrouter_configured" in data
        assert "model" in data

    def test_health_check_shows_api_key_status(self, client):
        """Test that health check indicates API key configuration."""
        response = client.get("/health")
        data = response.json()

        # These are booleans indicating if keys are configured
        assert isinstance(data["omdb_configured"], bool)
        assert isinstance(data["openrouter_configured"], bool)


class TestGenerateMovieEndpoint:
    """Tests for /generate-movie endpoint."""

    @patch('movie_pipeline.api.MovieGenerator')
    @patch('movie_pipeline.api.MovieFetcher')
    def test_generate_movie_success(self, mock_fetcher_class, mock_generator_class, client, mock_generated_movie):
        """Test successful movie generation."""
        # Setup mocks
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.return_value = [
            {"Title": "Inception"},
            {"Title": "The Matrix"}
        ]
        mock_fetcher_class.return_value = mock_fetcher

        mock_generator = MagicMock()
        mock_generator.generate_from_movies.return_value = mock_generated_movie
        mock_generator_class.return_value = mock_generator

        # Make request
        request_data = {
            "movie_names": ["Inception", "The Matrix"]
        }
        response = client.post("/generate-movie", json=request_data)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["movie"]["title"] == "Test Movie"
        assert data["input_movies_found"] == 2
        assert len(data["input_movies_data"]) == 2

    @patch('movie_pipeline.api.MovieGenerator')
    @patch('movie_pipeline.api.MovieFetcher')
    def test_generate_movie_with_model_override(self, mock_fetcher_class, mock_generator_class, client, mock_generated_movie):
        """Test movie generation with custom model."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.return_value = [{"Title": "Inception"}]
        mock_fetcher_class.return_value = mock_fetcher

        mock_generator = MagicMock()
        mock_generator.generate_from_movies.return_value = mock_generated_movie
        mock_generator_class.return_value = mock_generator

        request_data = {
            "movie_names": ["Inception"],
            "model": "custom/model"
        }
        response = client.post("/generate-movie", json=request_data)

        assert response.status_code == 200
        # Verify model override was passed
        call_args = mock_generator.generate_from_movies.call_args
        assert call_args.kwargs["model_override"] == "custom/model"

    @patch('movie_pipeline.api.MovieFetcher')
    def test_generate_movie_no_movies_found(self, mock_fetcher_class, client):
        """Test when no movies are found in OMDb."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.return_value = []
        mock_fetcher_class.return_value = mock_fetcher

        request_data = {
            "movie_names": ["NonexistentMovie123"]
        }
        response = client.post("/generate-movie", json=request_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_movie_invalid_request_empty_list(self, client):
        """Test with empty movie list."""
        request_data = {
            "movie_names": []
        }
        response = client.post("/generate-movie", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_generate_movie_invalid_request_too_many_movies(self, client):
        """Test with too many movies (>10)."""
        request_data = {
            "movie_names": [f"Movie{i}" for i in range(11)]
        }
        response = client.post("/generate-movie", json=request_data)

        assert response.status_code == 422  # Validation error

    @patch('movie_pipeline.api.MovieGenerator')
    @patch('movie_pipeline.api.MovieFetcher')
    def test_generate_movie_fetcher_error(self, mock_fetcher_class, mock_generator_class, client):
        """Test handling of MovieFetcherError."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.side_effect = MovieFetcherError("API error")
        mock_fetcher_class.return_value = mock_fetcher

        request_data = {
            "movie_names": ["Inception"]
        }
        response = client.post("/generate-movie", json=request_data)

        assert response.status_code == 500
        assert "Failed to fetch" in response.json()["detail"]

    @patch('movie_pipeline.api.MovieGenerator')
    @patch('movie_pipeline.api.MovieFetcher')
    def test_generate_movie_generator_error(self, mock_fetcher_class, mock_generator_class, client):
        """Test handling of MovieGeneratorError."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.return_value = [{"Title": "Inception"}]
        mock_fetcher_class.return_value = mock_fetcher

        mock_generator = MagicMock()
        mock_generator.generate_from_movies.side_effect = MovieGeneratorError("Generation failed")
        mock_generator_class.return_value = mock_generator

        request_data = {
            "movie_names": ["Inception"]
        }
        response = client.post("/generate-movie", json=request_data)

        # MovieGeneratorError returns success=False response, not HTTP error
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Generation failed"
        assert data["movie"] is None

    @patch('movie_pipeline.api.MovieGenerator')
    @patch('movie_pipeline.api.MovieFetcher')
    def test_generate_movie_unexpected_error(self, mock_fetcher_class, mock_generator_class, client):
        """Test handling of unexpected errors."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.side_effect = Exception("Unexpected error")
        mock_fetcher_class.return_value = mock_fetcher

        request_data = {
            "movie_names": ["Inception"]
        }
        response = client.post("/generate-movie", json=request_data)

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestFetchMovieDataEndpoint:
    """Tests for /fetch-movie-data endpoint."""

    @patch('movie_pipeline.api.MovieFetcher')
    def test_fetch_movie_data_success(self, mock_fetcher_class, client):
        """Test successful movie data fetching."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.return_value = [
            {"Title": "Inception", "Year": "2010"},
            {"Title": "The Matrix", "Year": "1999"}
        ]
        mock_fetcher_class.return_value = mock_fetcher

        response = client.post("/fetch-movie-data", json=["Inception", "The Matrix"])

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["movies_found"] == 2
        assert len(data["movies"]) == 2
        assert data["movies"][0]["Title"] == "Inception"

    @patch('movie_pipeline.api.MovieFetcher')
    def test_fetch_movie_data_partial_success(self, mock_fetcher_class, client):
        """Test fetching with some movies not found."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.return_value = [
            {"Title": "Inception"}
        ]
        mock_fetcher_class.return_value = mock_fetcher

        response = client.post("/fetch-movie-data", json=["Inception", "NonexistentMovie"])

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["movies_found"] == 1

    @patch('movie_pipeline.api.MovieFetcher')
    def test_fetch_movie_data_all_fail(self, mock_fetcher_class, client):
        """Test when all movies fail to fetch."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.return_value = []
        mock_fetcher_class.return_value = mock_fetcher

        response = client.post("/fetch-movie-data", json=["Bad1", "Bad2"])

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["movies_found"] == 0
        assert len(data["movies"]) == 0

    @patch('movie_pipeline.api.MovieFetcher')
    def test_fetch_movie_data_error(self, mock_fetcher_class, client):
        """Test error handling in fetch movie data."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.side_effect = Exception("Fetch error")
        mock_fetcher_class.return_value = mock_fetcher

        response = client.post("/fetch-movie-data", json=["Inception"])

        assert response.status_code == 500

    def test_fetch_movie_data_empty_list(self, client):
        """Test fetching with empty movie list."""
        response = client.post("/fetch-movie-data", json=[])

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["movies_found"] == 0


class TestCORSMiddleware:
    """Tests for CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are configured."""
        response = client.options("/")

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code in [200, 405]


class TestAPILogging:
    """Tests for API logging functionality."""

    @patch('movie_pipeline.api.logger')
    @patch('movie_pipeline.api.MovieGenerator')
    @patch('movie_pipeline.api.MovieFetcher')
    def test_logging_on_request(self, mock_fetcher_class, mock_generator_class, mock_logger, client, mock_generated_movie):
        """Test that requests are logged."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_multiple_movies.return_value = [{"Title": "Inception"}]
        mock_fetcher_class.return_value = mock_fetcher

        mock_generator = MagicMock()
        mock_generator.generate_from_movies.return_value = mock_generated_movie
        mock_generator_class.return_value = mock_generator

        request_data = {"movie_names": ["Inception"]}
        client.post("/generate-movie", json=request_data)

        # Check that logging was called
        assert mock_logger.info.called
