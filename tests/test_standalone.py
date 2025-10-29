"""
Standalone test script for the movie pipeline.

This script allows testing the movie generation pipeline from the command line
without running the API server.
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.movie_pipeline.movie_fetcher import MovieFetcher, MovieFetcherError
from src.movie_pipeline.movie_generator import MovieGenerator, MovieGeneratorError
from src.movie_pipeline.config import settings


def test_movie_fetching(movie_names):
    """Test fetching movies from OMDb."""
    print("\n" + "="*80)
    print("STEP 1: Fetching Movie Data from OMDb")
    print("="*80)

    fetcher = MovieFetcher()
    movies = []

    for movie_name in movie_names:
        print(f"\nFetching: {movie_name}")
        try:
            movie = fetcher.fetch_movie_by_title(movie_name)
            movies.append(movie)
            print(f"  ✓ Found: {movie.get('Title')} ({movie.get('Year')})")
            print(f"    Genre: {movie.get('Genre')}")
            print(f"    IMDb Rating: {movie.get('imdbRating')}/10")
        except MovieFetcherError as e:
            print(f"  ✗ Error: {e}")

    return movies


def test_movie_generation(movies, model=None):
    """Test generating a new movie concept."""
    print("\n" + "="*80)
    print("STEP 2: Generating New Movie Concept")
    print("="*80)

    if not movies:
        print("\n✗ No movies available to generate from!")
        return None

    print(f"\nUsing {len(movies)} movies as inspiration...")
    print(f"Model: {model or settings.openrouter_model}")

    generator = MovieGenerator()

    try:
        generated_movie = generator.generate_from_movies(movies, model_override=model)
        return generated_movie
    except MovieGeneratorError as e:
        print(f"\n✗ Generation Error: {e}")
        return None


def display_generated_movie(movie):
    """Display the generated movie details."""
    print("\n" + "="*80)
    print("GENERATED MOVIE CONCEPT")
    print("="*80)

    if not movie:
        print("\n✗ No movie was generated")
        return

    print(f"\nTitle: {movie.title}")
    print(f"Tagline: {movie.tagline}")
    print(f"\nGenres: {', '.join(movie.genres)}")

    print(f"\nDirector: {movie.director_name}")
    print(f"  Background: {movie.director_background}")

    print(f"\nWriters: {', '.join(movie.writers)}")
    print(f"  Background: {movie.writer_backgrounds}")

    print(f"\nRuntime: {movie.runtime}")
    print(f"Rating: {movie.rating}")
    print(f"Release Year: {movie.release_year}")
    print(f"Budget: {movie.budget}")

    print(f"\nProduction Company: {movie.production_company}")
    print(f"  Background: {movie.production_company_background}")

    print(f"\nPlot Summary:")
    print(f"{movie.plot_summary}")

    print(f"\n" + "="*80)
    print("CAST (Fictional Actors)")
    print("="*80)
    for i, cast_member in enumerate(movie.cast, 1):
        print(f"\n[{i}] {cast_member.actor_name} as {cast_member.character_name}")
        print(f"    Physical Description: {cast_member.physical_description}")
        print(f"    Traits: {', '.join(cast_member.personality_traits)}")
        print(f"    Acting Style: {cast_member.acting_style}")
        print(f"    Role: {cast_member.role_description}")

    print(f"\nThemes: {', '.join(movie.themes)}")

    print(f"\nVisual Style:")
    print(f"{movie.visual_style}")

    print(f"\nTarget Audience:")
    print(f"{movie.target_audience}")

    if movie.unique_selling_point:
        print(f"\nUnique Selling Point:")
        print(f"{movie.unique_selling_point}")

    if movie.similar_movies:
        print(f"\nSimilar Movies: {', '.join(movie.similar_movies)}")

    print(f"\nInspiration Sources: {', '.join(movie.inspiration_source)}")


def save_to_json(movie, filename="generated_movie.json"):
    """Save generated movie to JSON file."""
    if not movie:
        print("\n✗ No movie to save")
        return

    output = movie.model_dump()

    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved to: {filename}")


def main():
    """Main function for standalone testing."""
    parser = argparse.ArgumentParser(
        description="Test the movie pipeline by generating a movie concept from existing movies"
    )
    parser.add_argument(
        "--movies",
        type=str,
        required=True,
        help="Comma-separated list of movie names (e.g., 'Inception,The Matrix,Interstellar')"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="OpenRouter model to use (overrides default)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="generated_movie.json",
        help="Output JSON file path (default: generated_movie.json)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save output to file"
    )

    args = parser.parse_args()

    # Parse movie names
    movie_names = [name.strip() for name in args.movies.split(",")]

    print("="*80)
    print("MOVIE PIPELINE STANDALONE TEST")
    print("="*80)
    print(f"\nInput Movies: {', '.join(movie_names)}")
    print(f"Output File: {args.output if not args.no_save else 'None (display only)'}")

    # Test fetching
    movies = test_movie_fetching(movie_names)

    if not movies:
        print("\n✗ Failed to fetch any movies. Please check your movie names and OMDb API key.")
        return 1

    # Test generation
    generated_movie = test_movie_generation(movies, model=args.model)

    if not generated_movie:
        print("\n✗ Failed to generate movie. Please check your OpenRouter API key and settings.")
        return 1

    # Display results
    display_generated_movie(generated_movie)

    # Save to file
    if not args.no_save:
        save_to_json(generated_movie, args.output)

    print("\n" + "="*80)
    print("✓ TEST COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
