"""
Movie generator using OpenRouter LLM API.
"""

import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .config import settings
from .schemas import GeneratedMovie


class MovieGeneratorError(Exception):
    """Base exception for movie generator errors."""
    pass


class MovieGenerator:
    """Generates movie ideas using OpenRouter LLM."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize the MovieGenerator.

        Args:
            api_key: OpenRouter API key. If not provided, uses settings.openrouter_api_key
            model: Model to use. If not provided, uses settings.openrouter_model
            base_url: Base URL for OpenRouter. If not provided, uses settings.openrouter_base_url
        """
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.openrouter_model
        self.base_url = base_url or settings.openrouter_base_url

        # Initialize OpenAI client with OpenRouter
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _create_generation_prompt(self, movies_context: str) -> str:
        """
        Create the prompt for movie generation.

        Args:
            movies_context: Formatted context with movie details

        Returns:
            Complete prompt for the LLM
        """
        prompt = f"""You are a creative Hollywood producer and screenwriter. Based on the following movies, generate a completely NEW movie concept that would appeal to fans of these films.

REFERENCE MOVIES:
{movies_context}

Your task is to create a detailed movie concept inspired by these films. The new movie should:
1. Capture similar themes, tone, or genre elements
2. Appeal to the same target audience
3. Have a unique and original story (not a sequel or direct copy)
4. Be commercially viable and marketable

Generate a comprehensive movie description in JSON format with the following fields:

{{
  "title": "An original, compelling movie title",
  "tagline": "A catchy one-line tagline",
  "genres": ["Genre1", "Genre2", "Genre3"],
  "plot_summary": "A detailed plot summary (3-4 paragraphs) covering the main story arc, key characters, conflicts, and resolution",
  "director": "Name of a fictional director (or suggest a real director who would be perfect for this)",
  "writers": ["Writer1", "Writer2"],
  "cast": [
    {{"actor": "Lead Actor Name", "role": "Character Name - brief description"}},
    {{"actor": "Supporting Actor", "role": "Character Name - brief description"}},
    {{"actor": "Supporting Actor", "role": "Character Name - brief description"}},
    {{"actor": "Supporting Actor", "role": "Character Name - brief description"}}
  ],
  "runtime": "Expected runtime (e.g., '142 min')",
  "rating": "MPAA rating (e.g., 'PG-13', 'R')",
  "release_year": 2026,
  "production_company": "Fictional or real production company",
  "budget": "Estimated budget (e.g., '$150M')",
  "themes": ["Theme1", "Theme2", "Theme3"],
  "visual_style": "Detailed description of the cinematography, color palette, and visual aesthetic",
  "target_audience": "Description of who this movie is for",
  "unique_selling_point": "What makes this movie special and marketable",
  "similar_movies": ["Movie1", "Movie2", "Movie3"]
}}

Be creative, detailed, and ensure the concept is cohesive and compelling. The plot should be original but clearly inspired by the reference movies' best elements.

IMPORTANT: Return ONLY the JSON object, no additional text or formatting."""

        return prompt

    def generate_movie(
        self,
        movies_context: str,
        model_override: Optional[str] = None
    ) -> GeneratedMovie:
        """
        Generate a new movie concept based on provided movies context.

        Args:
            movies_context: Formatted string with movie details
            model_override: Optional model to use instead of default

        Returns:
            GeneratedMovie object with the generated movie details

        Raises:
            MovieGeneratorError: If generation fails
        """
        model_to_use = model_override or self.model
        prompt = self._create_generation_prompt(movies_context)

        try:
            # Create chat completion
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative film producer and screenwriter who generates detailed, original movie concepts. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,  # Higher temperature for more creativity
                max_tokens=4000,
            )

            # Extract the generated content
            content = response.choices[0].message.content

            if not content:
                raise MovieGeneratorError("Empty response from LLM")

            # Parse JSON response
            try:
                # Try to extract JSON if there's extra text
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    content = content[json_start:json_end]

                movie_data = json.loads(content)
            except json.JSONDecodeError as e:
                raise MovieGeneratorError(f"Failed to parse LLM response as JSON: {e}\nResponse: {content}")

            # Validate and create GeneratedMovie object
            try:
                generated_movie = GeneratedMovie(**movie_data)
                return generated_movie
            except Exception as e:
                raise MovieGeneratorError(f"Failed to validate generated movie data: {e}\nData: {movie_data}")

        except Exception as e:
            if isinstance(e, MovieGeneratorError):
                raise
            raise MovieGeneratorError(f"Failed to generate movie: {str(e)}")

    def generate_from_movies(
        self,
        movies: List[Dict[str, Any]],
        model_override: Optional[str] = None
    ) -> GeneratedMovie:
        """
        Generate a movie from a list of movie data dictionaries.

        Args:
            movies: List of movie data from OMDb API
            model_override: Optional model to use instead of default

        Returns:
            GeneratedMovie object

        Raises:
            MovieGeneratorError: If generation fails
        """
        if not movies:
            raise MovieGeneratorError("No movies provided for generation")

        # Import here to avoid circular dependency
        from .movie_fetcher import MovieFetcher

        fetcher = MovieFetcher()
        movies_context = fetcher.format_movies_for_context(movies)

        return self.generate_movie(movies_context, model_override)
