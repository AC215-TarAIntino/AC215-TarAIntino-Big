"""
Movie generator using OpenRouter LLM API.
"""

import json
from typing import Any

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
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
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
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

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

⚠️ CRITICAL REQUIREMENTS - NO COPYRIGHTED CONTENT:
- ALL names must be COMPLETELY FICTIONAL (no real actors, directors, writers, or production companies)
- Create detailed descriptions for everything since nothing can reference existing people/entities
- This will be used to actually generate a movie with AI, so descriptions must be comprehensive

Generate a comprehensive movie description in JSON format with the following fields:

{{
  "title": "An original, compelling movie title",
  "tagline": "A catchy one-line tagline",
  "genres": ["Genre1", "Genre2", "Genre3"],
  "plot_summary": "A detailed plot summary (3-4 paragraphs) covering the main story arc, key characters, conflicts, and resolution",

  "director_name": "FICTIONAL director name (make up a realistic but completely fake name)",
  "director_background": "Director's background, filmmaking style, previous work themes, and approach (3-4 sentences describing their fictional career and artistic vision)",

  "writers": ["FICTIONAL Writer Name 1", "FICTIONAL Writer Name 2"],
  "writer_backgrounds": "Brief description of these fictional writers' backgrounds, specialties, and writing styles (2-3 sentences)",

  "cast": [
    {{
      "actor_name": "FICTIONAL actor name (completely made up, not a real person)",
      "character_name": "Character name in the movie",
      "physical_description": "DETAILED physical appearance: height in feet only (e.g., \"about 6 feet tall\"), build (e.g., athletic, lean), age range, ethnicity, hair color and style, eye color, facial features (e.g., sharp jawline, warm eyes), distinctive characteristics (e.g., scar, tattoos, mannerisms). Minimum 5-7 sentences with vivid detail so an AI can visualize them. Do NOT use apostrophes or quotes for measurements.",
      "personality_traits": ["trait1", "trait2", "trait3", "trait4"],
      "acting_style": "Description of their acting approach and screen presence (e.g., 'Intense method actor with exceptional emotional range' or 'Charismatic performer known for physical comedy and timing')",
      "role_description": "Detailed description of the character they play and their importance to the story (3-4 sentences)"
    }},
    {{
      "actor_name": "FICTIONAL actor name",
      "character_name": "Character name",
      "physical_description": "Detailed physical description (5-7 sentences minimum)",
      "personality_traits": ["trait1", "trait2", "trait3"],
      "acting_style": "Acting approach description",
      "role_description": "Character role details"
    }},
    {{
      "actor_name": "FICTIONAL actor name",
      "character_name": "Character name",
      "physical_description": "Detailed physical description (5-7 sentences minimum)",
      "personality_traits": ["trait1", "trait2", "trait3"],
      "acting_style": "Acting approach description",
      "role_description": "Character role details"
    }},
    {{
      "actor_name": "FICTIONAL actor name",
      "character_name": "Character name",
      "physical_description": "Detailed physical description (5-7 sentences minimum)",
      "personality_traits": ["trait1", "trait2", "trait3"],
      "acting_style": "Acting approach description",
      "role_description": "Character role details"
    }}
  ],

  "runtime": "Expected runtime (e.g., '142 min')",
  "rating": "MPAA rating (e.g., 'PG-13', 'R')",
  "release_year": 2026,

  "production_company": "FICTIONAL production company name (completely made up, not a real company)",
  "production_company_background": "Production company's background: what types of films they're known for, their size/scope (indie vs. major studio), their creative reputation (2-3 sentences)",

  "budget": "Estimated budget (e.g., '$150M')",
  "themes": ["Theme1", "Theme2", "Theme3"],
  "visual_style": "Detailed description of the cinematography, color palette, shot composition, and visual aesthetic (4-5 sentences)",
  "target_audience": "Description of who this movie is for",
  "unique_selling_point": "What makes this movie special and marketable",
  "similar_movies": ["Movie1", "Movie2", "Movie3"]
}}

REMEMBER:
- NO real actor names (not Oscar Isaac, not Adam Driver, not anyone real)
- NO real director names (not Denis Villeneuve, not Christopher Nolan, not anyone real)
- NO real production companies (not A24, not Warner Bros, not anyone real)
- EVERY actor needs extensive physical descriptions (5-7 sentences minimum with height, build, age, ethnicity, hair, eyes, features)
- Be creative with fictional names that sound professional but are completely made up

Be creative, detailed, and ensure the concept is cohesive and compelling. The plot should be original but clearly inspired by the reference movies' best elements.

IMPORTANT: Return ONLY the JSON object, no additional text or formatting."""

        return prompt

    def generate_movie(
        self, movies_context: str, model_override: str | None = None
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
                        "content": "You are a creative film producer and screenwriter who generates detailed, original movie concepts. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,  # Higher temperature for more creativity
                max_tokens=8000,  # Increased for detailed actor/director descriptions
            )

            # Extract the generated content
            content = response.choices[0].message.content

            if not content:
                raise MovieGeneratorError("Empty response from LLM")

            # Parse JSON response with enhanced error handling for Llama models
            try:
                # Try to extract JSON if there's extra text
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    content = content[json_start:json_end]

                # Try strict parsing first
                try:
                    movie_data = json.loads(content)
                except json.JSONDecodeError:
                    # If strict parsing fails, try to fix common JSON issues
                    import re

                    # Fix 1: Replace newlines within strings with spaces
                    # This regex finds newlines that are inside quoted strings
                    content = content.replace("\n\n", " ")  # Double newlines first
                    content = content.replace("\n", " ")  # Then single newlines

                    # Fix 2: Remove trailing commas before closing brackets/braces
                    content = re.sub(r",(\s*[}\]])", r"\1", content)

                    # Fix 3: Fix missing commas between fields (common Claude/Llama issue)
                    content = re.sub(r'"\s*"', '", "', content)

                    # Fix missing commas after closing braces/brackets before quotes or braces
                    content = re.sub(r'}\s*"', '}, "', content)  # } " -> }, "
                    content = re.sub(r'}\s*{', '}, {', content)  # } { -> }, {
                    content = re.sub(r']\s*"', '], "', content)  # ] " -> ], "
                    content = re.sub(r']\s*{', '], {', content)  # ] { -> ], {
                    content = re.sub(r']\s*\[', '], [', content)  # ] [ -> ], [

                    # Fix 4: Remove comments if any
                    content = re.sub(r'//.*?\n', '', content)
                    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

                    # Fix 5: Fix common quote escaping issues
                    content = content.replace('\\"', '"').replace("'", '"')

                    # Try parsing again
                    movie_data = json.loads(content)
            except json.JSONDecodeError as e:
                raise MovieGeneratorError(
                    f"Failed to parse LLM response as JSON: {e}\nResponse: {content}"
                ) from e

            # Validate and create GeneratedMovie object
            try:
                generated_movie = GeneratedMovie(**movie_data)
                return generated_movie
            except Exception as e:
                raise MovieGeneratorError(
                    f"Failed to validate generated movie data: {e}\nData: {movie_data}"
                ) from e

        except Exception as e:
            if isinstance(e, MovieGeneratorError):
                raise
            raise MovieGeneratorError(f"Failed to generate movie: {str(e)}") from e

    def generate_from_movies(
        self, movies: list[dict[str, Any]], model_override: str | None = None
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

        generated_movie = self.generate_movie(movies_context, model_override)

        # Populate inspiration_source if not provided by LLM
        if not generated_movie.inspiration_source:
            generated_movie.inspiration_source = [movie.get("Title", "Unknown") for movie in movies]

        return generated_movie
