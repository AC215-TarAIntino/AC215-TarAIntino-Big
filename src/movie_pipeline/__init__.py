"""
Movie Pipeline Module

A module for generating movie ideas inspired by existing movies.
Uses OMDb API for movie data and OpenRouter for LLM generation.
"""

__version__ = "0.1.0"

from .movie_fetcher import MovieFetcher
from .movie_generator import MovieGenerator
from .schemas import MovieRequest, GeneratedMovie

__all__ = ["MovieFetcher", "MovieGenerator", "MovieRequest", "GeneratedMovie"]
