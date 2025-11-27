"""
Tests for the movie fetcher module.
"""

import pytest
import requests
from unittest.mock import Mock, patch
from movie_pipeline.movie_fetcher import (
    MovieFetcher,
    MovieFetcherError,
    MovieNotFoundError
)


@pytest.fixture
def mock_omdb_response():
    """Fixture providing a mock OMDb API response."""
    return {
        "Title": "Inception",
        "Year": "2010",
        "Director": "Christopher Nolan",
        "Writer": "Christopher Nolan",
        "Actors": "Leonardo DiCaprio, Joseph Gordon-Levitt",
        "Genre": "Action, Sci-Fi, Thriller",
        "Runtime": "148 min",
        "Rated": "PG-13",
        "imdbRating": "8.8",
        "Plot": "A thief who steals corporate secrets through dream-sharing technology.",
        "Awards": "Won 4 Oscars",
        "BoxOffice": "$292,587,330",
        "Production": "Warner Bros.",
        "Country": "USA, UK",
        "Language": "English",
        "Response": "True"
    }


class TestMovieFetcher:
    """Tests for MovieFetcher class."""

    def test_init_with_custom_api_key(self):
        """Test MovieFetcher initialization with custom API key."""
        fetcher = MovieFetcher(api_key="custom_key")
        assert fetcher.api_key == "custom_key"
        assert fetcher.base_url == "http://www.omdbapi.com/"

    def test_init_with_default_api_key(self):
        """Test MovieFetcher initialization with default API key from settings."""
        fetcher = MovieFetcher()
        assert fetcher.api_key is not None
        assert isinstance(fetcher.api_key, str)

    @patch('movie_pipeline.movie_fetcher.requests.get')
    def test_fetch_movie_by_title_success(self, mock_get, mock_omdb_response):
        """Test successfully fetching a movie by title."""
        mock_response = Mock()
        mock_response.json.return_value = mock_omdb_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = MovieFetcher(api_key="test_key")
        result = fetcher.fetch_movie_by_title("Inception")

        assert result["Title"] == "Inception"
        assert result["Year"] == "2010"
        assert result["Director"] == "Christopher Nolan"
        mock_get.assert_called_once()

    @patch('movie_pipeline.movie_fetcher.requests.get')
    def test_fetch_movie_by_title_with_year(self, mock_get, mock_omdb_response):
        """Test fetching a movie by title and year."""
        mock_response = Mock()
        mock_response.json.return_value = mock_omdb_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = MovieFetcher(api_key="test_key")
        result = fetcher.fetch_movie_by_title("Inception", year="2010")

        # Check that year parameter was passed
        call_args = mock_get.call_args
        assert "y" in call_args.kwargs["params"]
        assert call_args.kwargs["params"]["y"] == "2010"

    @patch('movie_pipeline.movie_fetcher.requests.get')
    def test_fetch_movie_not_found(self, mock_get):
        """Test handling when movie is not found."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Response": "False",
            "Error": "Movie not found!"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = MovieFetcher(api_key="test_key")

        with pytest.raises(MovieNotFoundError) as exc_info:
            fetcher.fetch_movie_by_title("NonexistentMovie123")

        assert "NonexistentMovie123" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    @patch('movie_pipeline.movie_fetcher.requests.get')
    def test_fetch_movie_request_exception(self, mock_get):
        """Test handling of requests exceptions."""
        mock_get.side_effect = requests.RequestException("Connection error")

        fetcher = MovieFetcher(api_key="test_key")

        with pytest.raises(MovieFetcherError) as exc_info:
            fetcher.fetch_movie_by_title("Inception")

        assert "Failed to fetch" in str(exc_info.value)
        assert "Connection error" in str(exc_info.value)

    @patch('movie_pipeline.movie_fetcher.requests.get')
    def test_fetch_movie_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        fetcher = MovieFetcher(api_key="test_key")

        with pytest.raises(MovieFetcherError):
            fetcher.fetch_movie_by_title("Inception")

    @patch('movie_pipeline.movie_fetcher.requests.get')
    def test_fetch_multiple_movies_success(self, mock_get, mock_omdb_response):
        """Test fetching multiple movies successfully."""
        mock_response = Mock()
        mock_response.json.return_value = mock_omdb_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = MovieFetcher(api_key="test_key")
        results = fetcher.fetch_multiple_movies(["Inception", "The Matrix"])

        assert len(results) == 2
        assert mock_get.call_count == 2

    @patch('movie_pipeline.movie_fetcher.requests.get')
    def test_fetch_multiple_movies_partial_success(self, mock_get, mock_omdb_response):
        """Test fetching multiple movies with some not found."""
        # First call succeeds, second fails
        def side_effect(*args, **kwargs):
            title = kwargs["params"]["t"]
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            if title == "Inception":
                mock_response.json.return_value = mock_omdb_response
            else:
                mock_response.json.return_value = {
                    "Response": "False",
                    "Error": "Movie not found!"
                }
            return mock_response

        mock_get.side_effect = side_effect

        fetcher = MovieFetcher(api_key="test_key")
        results = fetcher.fetch_multiple_movies(["Inception", "NonexistentMovie"])

        # Should return only the successful one
        assert len(results) == 1
        assert results[0]["Title"] == "Inception"

    @patch('movie_pipeline.movie_fetcher.requests.get')
    def test_fetch_multiple_movies_all_fail(self, mock_get):
        """Test fetching multiple movies when all fail."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Response": "False",
            "Error": "Movie not found!"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = MovieFetcher(api_key="test_key")
        results = fetcher.fetch_multiple_movies(["Bad1", "Bad2"])

        assert len(results) == 0

    def test_format_movie_for_context(self, mock_omdb_response):
        """Test formatting a single movie for LLM context."""
        fetcher = MovieFetcher(api_key="test_key")
        formatted = fetcher.format_movie_for_context(mock_omdb_response)

        assert "Title: Inception" in formatted
        assert "Year: 2010" in formatted
        assert "Director: Christopher Nolan" in formatted
        assert "Genre: Action, Sci-Fi, Thriller" in formatted
        assert "IMDb Rating: 8.8/10" in formatted

    def test_format_movie_for_context_missing_fields(self):
        """Test formatting a movie with missing fields."""
        incomplete_data = {
            "Title": "Test Movie",
            "Year": "2020"
            # Many fields missing
        }

        fetcher = MovieFetcher(api_key="test_key")
        formatted = fetcher.format_movie_for_context(incomplete_data)

        assert "Title: Test Movie" in formatted
        assert "Year: 2020" in formatted
        assert "N/A" in formatted  # Should have N/A for missing fields

    def test_format_movies_for_context(self, mock_omdb_response):
        """Test formatting multiple movies for LLM context."""
        movies = [
            mock_omdb_response,
            {**mock_omdb_response, "Title": "The Matrix"}
        ]

        fetcher = MovieFetcher(api_key="test_key")
        formatted = fetcher.format_movies_for_context(movies)

        assert "=== Movie 1 ===" in formatted
        assert "=== Movie 2 ===" in formatted
        assert "Title: Inception" in formatted
        assert "Title: The Matrix" in formatted

    def test_format_movies_for_context_single_movie(self, mock_omdb_response):
        """Test formatting a single movie in list."""
        fetcher = MovieFetcher(api_key="test_key")
        formatted = fetcher.format_movies_for_context([mock_omdb_response])

        assert "=== Movie 1 ===" in formatted
        assert "Title: Inception" in formatted
        # Should not have Movie 2
        assert "=== Movie 2 ===" not in formatted

    def test_format_movies_for_context_empty_list(self):
        """Test formatting an empty movie list."""
        fetcher = MovieFetcher(api_key="test_key")
        formatted = fetcher.format_movies_for_context([])

        assert formatted == ""


class TestMovieFetcherExceptions:
    """Tests for MovieFetcher exception classes."""

    def test_movie_fetcher_error_inheritance(self):
        """Test that MovieFetcherError inherits from Exception."""
        error = MovieFetcherError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_movie_not_found_error_inheritance(self):
        """Test that MovieNotFoundError inherits from MovieFetcherError."""
        error = MovieNotFoundError("Movie not found")
        assert isinstance(error, MovieFetcherError)
        assert isinstance(error, Exception)
        assert str(error) == "Movie not found"
