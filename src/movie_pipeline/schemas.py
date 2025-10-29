"""
Pydantic schemas for request/response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MovieRequest(BaseModel):
    """Request schema for movie generation."""

    movie_names: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of movie names to use as inspiration (1-10 movies)",
        examples=[["Inception", "The Matrix", "Interstellar"]]
    )

    model: Optional[str] = Field(
        None,
        description="OpenRouter model to use (overrides default)",
        examples=["google/gemini-2.0-flash-exp:free", "anthropic/claude-3.5-sonnet"]
    )


class CastMember(BaseModel):
    """A cast member with their role."""

    actor: str = Field(..., description="Actor name")
    role: str = Field(..., description="Character name or role description")


class GeneratedMovie(BaseModel):
    """Response schema for generated movie."""

    title: str = Field(..., description="Generated movie title")

    tagline: str = Field(..., description="Catchy tagline for the movie")

    genres: List[str] = Field(
        ...,
        description="List of genres",
        examples=[["Sci-Fi", "Thriller", "Action"]]
    )

    plot_summary: str = Field(
        ...,
        description="Comprehensive plot summary of the movie"
    )

    director: str = Field(..., description="Fictional director name")

    writers: List[str] = Field(..., description="List of fictional writer names")

    cast: List[CastMember] = Field(
        ...,
        description="Main cast members with their roles"
    )

    runtime: str = Field(
        ...,
        description="Expected runtime in minutes",
        examples=["148 min"]
    )

    rating: str = Field(
        ...,
        description="MPAA rating",
        examples=["PG-13", "R", "PG"]
    )

    release_year: int = Field(
        ...,
        description="Proposed release year",
        ge=2024,
        le=2030
    )

    production_company: str = Field(
        ...,
        description="Fictional production company"
    )

    budget: str = Field(
        ...,
        description="Estimated budget",
        examples=["$150M", "$80M"]
    )

    themes: List[str] = Field(
        ...,
        description="Major themes explored in the movie"
    )

    visual_style: str = Field(
        ...,
        description="Description of the movie's visual aesthetic and cinematography"
    )

    target_audience: str = Field(
        ...,
        description="Description of the target audience"
    )

    inspiration_source: Optional[List[str]] = Field(
        None,
        description="Original movies that inspired this concept"
    )

    unique_selling_point: Optional[str] = Field(
        None,
        description="What makes this movie unique or marketable"
    )

    similar_movies: Optional[List[str]] = Field(
        None,
        description="Movies with similar themes or style (for marketing)"
    )


class MovieGenerationResponse(BaseModel):
    """Complete API response with metadata."""

    model_config = {"protected_namespaces": ()}

    success: bool = Field(..., description="Whether generation was successful")

    movie: Optional[GeneratedMovie] = Field(
        None,
        description="Generated movie details (null if failed)"
    )

    input_movies_found: int = Field(
        ...,
        description="Number of input movies successfully found in OMDb"
    )

    input_movies_data: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Original movie data from OMDb (optional)"
    )

    error: Optional[str] = Field(
        None,
        description="Error message if generation failed"
    )

    model_used: str = Field(..., description="OpenRouter model that was used")
