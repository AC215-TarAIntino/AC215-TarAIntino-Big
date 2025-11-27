"""
Tests for the movie generator module.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from movie_pipeline.movie_generator import MovieGenerator, MovieGeneratorError
from movie_pipeline.schemas import GeneratedMovie


@pytest.fixture
def valid_llm_response():
    """Fixture providing a valid LLM JSON response."""
    return json.dumps(
        {
            "title": "Quantum Echoes",
            "tagline": "Time is the ultimate prison",
            "genres": ["Sci-Fi", "Thriller", "Drama"],
            "plot_summary": "A physicist discovers a way to send messages to the past.",
            "director_name": "Elena Visionmaker",
            "director_background": "Independent filmmaker known for cerebral sci-fi.",
            "writers": ["Marcus Wordsmith", "Sara Storyteller"],
            "writer_backgrounds": "Acclaimed duo specializing in hard science fiction.",
            "cast": [
                {
                    "actor_name": "Jordan Performer",
                    "character_name": "Dr. Alex Quantum",
                    "physical_description": "Tall individual in their 40s with intense eyes.",
                    "personality_traits": ["brilliant", "obsessive", "isolated"],
                    "acting_style": "Method actor with technical precision",
                    "role_description": "Lead physicist who makes the breakthrough discovery",
                }
            ],
            "runtime": "135 min",
            "rating": "PG-13",
            "release_year": 2026,
            "production_company": "Stellar Pictures",
            "production_company_background": "Indie studio focused on intelligent genre films.",
            "budget": "$60M",
            "themes": ["time", "consequence", "isolation"],
            "visual_style": "Cold, clinical aesthetic with bursts of color.",
            "target_audience": "Adults 25-50 interested in thought-provoking sci-fi",
        }
    )


@pytest.fixture
def mock_openai_client():
    """Fixture providing a mocked OpenAI client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Setup the nested structure
    mock_message.content = None  # Will be set in tests
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    return mock_client, mock_response, mock_message


class TestMovieGenerator:
    """Tests for MovieGenerator class."""

    def test_init_with_custom_parameters(self):
        """Test MovieGenerator initialization with custom parameters."""
        generator = MovieGenerator(
            api_key="custom_key", model="custom/model", base_url="https://custom.url"
        )

        assert generator.api_key == "custom_key"
        assert generator.model == "custom/model"
        assert generator.base_url == "https://custom.url"

    def test_init_with_default_parameters(self):
        """Test MovieGenerator initialization with default parameters."""
        generator = MovieGenerator()

        assert generator.api_key is not None
        assert generator.model is not None
        assert generator.base_url is not None
        assert generator.client is not None

    def test_create_generation_prompt(self):
        """Test that generation prompt is created correctly."""
        generator = MovieGenerator()
        context = "Title: Inception\nYear: 2010"

        prompt = generator._create_generation_prompt(context)

        assert "Inception" in prompt
        assert "2010" in prompt
        assert "JSON" in prompt
        assert "FICTIONAL" in prompt
        assert "title" in prompt
        assert "genres" in prompt

    def test_create_generation_prompt_structure(self):
        """Test that prompt includes all required fields."""
        generator = MovieGenerator()
        prompt = generator._create_generation_prompt("Test context")

        # Check that all required fields are mentioned in prompt
        required_fields = [
            "title",
            "tagline",
            "genres",
            "plot_summary",
            "director_name",
            "writers",
            "cast",
            "runtime",
            "rating",
            "release_year",
            "budget",
            "themes",
        ]

        for field in required_fields:
            assert field in prompt

    @patch("movie_pipeline.movie_generator.OpenAI")
    def test_generate_movie_success(self, mock_openai_class, valid_llm_response):
        """Test successfully generating a movie."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        mock_message.content = valid_llm_response
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        generator = MovieGenerator(api_key="test_key")
        context = "Title: Inception\nYear: 2010"

        result = generator.generate_movie(context)

        assert isinstance(result, GeneratedMovie)
        assert result.title == "Quantum Echoes"
        assert len(result.genres) == 3
        assert result.release_year == 2026

    @patch("movie_pipeline.movie_generator.OpenAI")
    def test_generate_movie_with_model_override(self, mock_openai_class, valid_llm_response):
        """Test generating a movie with model override."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        mock_message.content = valid_llm_response
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        generator = MovieGenerator(api_key="test_key", model="default/model")
        context = "Test context"

        generator.generate_movie(context, model_override="override/model")

        # Check that the override model was used
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "override/model"

    @patch("movie_pipeline.movie_generator.OpenAI")
    def test_generate_movie_empty_response(self, mock_openai_class):
        """Test handling of empty LLM response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        mock_message.content = None
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        generator = MovieGenerator(api_key="test_key")

        with pytest.raises(MovieGeneratorError) as exc_info:
            generator.generate_movie("context")

        assert "Empty response" in str(exc_info.value)

    @patch("movie_pipeline.movie_generator.OpenAI")
    def test_generate_movie_invalid_json(self, mock_openai_class):
        """Test handling of invalid JSON response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        mock_message.content = "This is not valid JSON at all"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        generator = MovieGenerator(api_key="test_key")

        with pytest.raises(MovieGeneratorError) as exc_info:
            generator.generate_movie("context")

        assert "Failed to parse" in str(exc_info.value)

    @patch("movie_pipeline.movie_generator.OpenAI")
    def test_generate_movie_json_with_extra_text(self, mock_openai_class, valid_llm_response):
        """Test handling JSON response with extra text around it."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        # Add extra text before and after JSON
        mock_message.content = f"Here's the movie:\n{valid_llm_response}\nHope you like it!"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        generator = MovieGenerator(api_key="test_key")
        result = generator.generate_movie("context")

        # Should still parse successfully
        assert isinstance(result, GeneratedMovie)
        assert result.title == "Quantum Echoes"

    @patch("movie_pipeline.movie_generator.OpenAI")
    def test_generate_movie_api_error(self, mock_openai_class):
        """Test handling of OpenAI API errors."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        generator = MovieGenerator(api_key="test_key")

        with pytest.raises(MovieGeneratorError) as exc_info:
            generator.generate_movie("context")

        assert "Failed to generate movie" in str(exc_info.value)

    @patch("movie_pipeline.movie_generator.OpenAI")
    @patch("movie_pipeline.movie_fetcher.MovieFetcher")
    def test_generate_from_movies_success(
        self, mock_fetcher_class, mock_openai_class, valid_llm_response
    ):
        """Test generating from movie data dictionaries."""
        # Setup OpenAI mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        mock_message.content = valid_llm_response
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Setup MovieFetcher mock
        mock_fetcher = MagicMock()
        mock_fetcher.format_movies_for_context.return_value = "Formatted context"
        mock_fetcher_class.return_value = mock_fetcher

        generator = MovieGenerator(api_key="test_key")
        movies = [{"Title": "Inception"}, {"Title": "The Matrix"}]

        result = generator.generate_from_movies(movies)

        assert isinstance(result, GeneratedMovie)
        assert result.title == "Quantum Echoes"
        assert result.inspiration_source == ["Inception", "The Matrix"]

    @patch("movie_pipeline.movie_generator.OpenAI")
    def test_generate_from_movies_empty_list(self, mock_openai_class):
        """Test generating from empty movie list raises error."""
        mock_openai_class.return_value = MagicMock()

        generator = MovieGenerator(api_key="test_key")

        with pytest.raises(MovieGeneratorError) as exc_info:
            generator.generate_from_movies([])

        assert "No movies provided" in str(exc_info.value)

    @patch("movie_pipeline.movie_generator.OpenAI")
    @patch("movie_pipeline.movie_fetcher.MovieFetcher")
    def test_generate_from_movies_with_inspiration_in_response(
        self, mock_fetcher_class, mock_openai_class, valid_llm_response
    ):
        """Test that inspiration_source in LLM response is preserved."""
        # Modify response to include inspiration_source
        response_data = json.loads(valid_llm_response)
        response_data["inspiration_source"] = ["Custom Movie 1", "Custom Movie 2"]
        modified_response = json.dumps(response_data)

        # Setup mocks
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()

        mock_message.content = modified_response
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        mock_fetcher = MagicMock()
        mock_fetcher.format_movies_for_context.return_value = "Context"
        mock_fetcher_class.return_value = mock_fetcher

        generator = MovieGenerator(api_key="test_key")
        movies = [{"Title": "Inception"}]

        result = generator.generate_from_movies(movies)

        # Should preserve the LLM-provided inspiration_source
        assert result.inspiration_source == ["Custom Movie 1", "Custom Movie 2"]


class TestMovieGeneratorErrors:
    """Tests for MovieGeneratorError exception."""

    def test_movie_generator_error_inheritance(self):
        """Test that MovieGeneratorError inherits from Exception."""
        error = MovieGeneratorError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
