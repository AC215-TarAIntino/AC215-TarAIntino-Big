"""
Movie data fetcher using OMDb API.
"""

import requests
from typing import Optional, Dict, Any, List
from .config import settings


class MovieFetcherError(Exception):
    """Base exception for movie fetcher errors."""
    pass


class MovieNotFoundError(MovieFetcherError):
    """Raised when a movie is not found in the OMDb database."""
    pass


class MovieFetcher:
    """Fetches movie information from OMDb API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the MovieFetcher.

        Args:
            api_key: OMDb API key. If not provided, uses settings.omdb_api_key
        """
        self.api_key = api_key or settings.omdb_api_key
        self.base_url = settings.omdb_base_url

    def fetch_movie_by_title(self, title: str, year: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch movie details by title.

        Args:
            title: Movie title to search for
            year: Optional year to narrow down search

        Returns:
            Dictionary containing movie details

        Raises:
            MovieNotFoundError: If movie is not found
            MovieFetcherError: If API request fails
        """
        params = {
            "apikey": self.api_key,
            "t": title,
            "plot": "full",  # Get full plot instead of short
            "type": "movie"
        }

        if year:
            params["y"] = year

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("Response") == "False":
                error_msg = data.get("Error", "Movie not found")
                raise MovieNotFoundError(f"Movie '{title}' not found: {error_msg}")

            return data

        except requests.RequestException as e:
            raise MovieFetcherError(f"Failed to fetch movie '{title}': {str(e)}")

    def fetch_multiple_movies(self, titles: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch details for multiple movies.

        Args:
            titles: List of movie titles

        Returns:
            List of movie detail dictionaries

        Note:
            Silently skips movies that are not found rather than raising an error.
        """
        movies = []
        for title in titles:
            try:
                movie_data = self.fetch_movie_by_title(title)
                movies.append(movie_data)
            except MovieNotFoundError as e:
                print(f"Warning: {e}")
                continue
            except MovieFetcherError as e:
                print(f"Error: {e}")
                continue

        return movies

    def format_movie_for_context(self, movie_data: Dict[str, Any]) -> str:
        """
        Format movie data into a structured text for LLM context.

        Args:
            movie_data: Raw movie data from OMDb API

        Returns:
            Formatted string representation of movie details
        """
        formatted = f"""
Title: {movie_data.get('Title', 'N/A')}
Year: {movie_data.get('Year', 'N/A')}
Director: {movie_data.get('Director', 'N/A')}
Writers: {movie_data.get('Writer', 'N/A')}
Cast: {movie_data.get('Actors', 'N/A')}
Genre: {movie_data.get('Genre', 'N/A')}
Runtime: {movie_data.get('Runtime', 'N/A')}
Rating: {movie_data.get('Rated', 'N/A')}
IMDb Rating: {movie_data.get('imdbRating', 'N/A')}/10
Plot: {movie_data.get('Plot', 'N/A')}
Awards: {movie_data.get('Awards', 'N/A')}
Box Office: {movie_data.get('BoxOffice', 'N/A')}
Production: {movie_data.get('Production', 'N/A')}
Country: {movie_data.get('Country', 'N/A')}
Language: {movie_data.get('Language', 'N/A')}
        """.strip()

        return formatted

    def format_movies_for_context(self, movies: List[Dict[str, Any]]) -> str:
        """
        Format multiple movies into a single context string for the LLM.

        Args:
            movies: List of movie data dictionaries

        Returns:
            Combined formatted string for all movies
        """
        formatted_movies = []
        for i, movie in enumerate(movies, 1):
            formatted_movies.append(f"=== Movie {i} ===\n{self.format_movie_for_context(movie)}")

        return "\n\n".join(formatted_movies)
