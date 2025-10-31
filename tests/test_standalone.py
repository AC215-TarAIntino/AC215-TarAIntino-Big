"""
Standalone test script for trailer generator.

Usage:
    python tests/test_standalone.py --movie-file path/to/movie.json
    python tests/test_standalone.py --movie-file path/to/movie.json --duration 45
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trailer_generator.schemas import GeneratedMovie, TrailerRequest
from trailer_generator.scene_generator import SceneGenerator, SceneGeneratorError


def load_movie_from_file(file_path: str) -> GeneratedMovie:
    """
    Load a movie from a JSON file.

    Args:
        file_path: Path to the movie JSON file

    Returns:
        GeneratedMovie object
    """
    try:
        with open(file_path, 'r') as f:
            movie_data = json.load(f)

        return GeneratedMovie(**movie_data)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading movie: {e}")
        sys.exit(1)


def save_trailer_to_json(trailer_data: dict, filename: str = "outputs/trailer_breakdown.json"):
    """
    Save trailer breakdown to JSON file.

    Args:
        trailer_data: Trailer breakdown dictionary
        filename: Output filename
    """
    # Ensure outputs directory exists
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(trailer_data, f, indent=2)

    print(f"\n✅ Trailer breakdown saved to: {output_path}")
    print(f"📊 File size: {output_path.stat().st_size / 1024:.2f} KB")


def display_trailer_summary(trailer_data: dict):
    """
    Display a summary of the generated trailer.

    Args:
        trailer_data: Trailer breakdown dictionary
    """
    print("\n" + "=" * 70)
    print(f"🎬 TRAILER BREAKDOWN: {trailer_data['movie_title']}")
    print("=" * 70)

    print(f"\n📹 Total Duration: {trailer_data['total_duration']} seconds")
    print(f"🎞️  Number of Scenes: {len(trailer_data['scenes'])}")

    if trailer_data.get('narration_script'):
        print(f"\n🎙️  Narration Script:")
        print(f"   {trailer_data['narration_script']}")

    print(f"\n🎨 Technical Specs:")
    specs = trailer_data['technical_specs']
    print(f"   Color Grading: {specs['color_grading']}")
    print(f"   Aspect Ratio: {specs['aspect_ratio']}")
    print(f"   Visual Style: {specs['visual_style'][:100]}...")

    print(f"\n🎭 Character Appearances:")
    for char, scenes in trailer_data['character_appearance_map'].items():
        print(f"   {char}: Scenes {', '.join(map(str, scenes))}")

    print(f"\n📋 Scene Breakdown:")
    for scene in trailer_data['scenes']:
        print(f"\n   Scene {scene['scene_number']}: {scene['scene_type'].upper()} ({scene['duration_seconds']}s)")
        print(f"   Characters: {', '.join(scene['characters_present']) or 'None'}")
        print(f"   Video Prompt: {scene['video_prompt'][:100]}...")

    print("\n" + "=" * 70)


def main():
    """Main function for standalone testing."""
    parser = argparse.ArgumentParser(
        description="Generate trailer scene breakdown from a movie JSON file"
    )

    parser.add_argument(
        "--movie-file",
        type=str,
        required=True,
        help="Path to movie JSON file (from mcp-screenplay)"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=35,
        help="Target trailer duration in seconds (20-60, default: 35)"
    )

    parser.add_argument(
        "--no-narration",
        action="store_true",
        help="Disable narration script generation"
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="OpenRouter model to use (default: from config)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="outputs/trailer_breakdown.json",
        help="Output JSON file path (default: outputs/trailer_breakdown.json)"
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save to file, only display output"
    )

    args = parser.parse_args()

    # Validate duration
    if not 20 <= args.duration <= 60:
        print("❌ Error: Duration must be between 20 and 60 seconds")
        sys.exit(1)

    print("🎬 Trailer Generator - Standalone Test")
    print("=" * 70)

    # Load movie
    print(f"\n📂 Loading movie from: {args.movie_file}")
    movie = load_movie_from_file(args.movie_file)
    print(f"✅ Loaded: {movie.title}")
    print(f"   Genres: {', '.join(movie.genres)}")
    print(f"   Cast: {len(movie.cast)} actors")

    # Generate trailer
    print(f"\n🤖 Generating trailer breakdown...")
    print(f"   Duration: {args.duration}s")
    print(f"   Narration: {'Yes' if not args.no_narration else 'No'}")
    if args.model:
        print(f"   Model: {args.model}")

    try:
        generator = SceneGenerator(model=args.model)

        trailer = generator.generate_trailer(
            movie=movie,
            target_duration=args.duration,
            include_narration=not args.no_narration
        )

        print("✅ Generation complete!")

        # Convert to dict for display/save
        trailer_data = trailer.model_dump()

        # Display summary
        display_trailer_summary(trailer_data)

        # Save to file
        if not args.no_save:
            save_trailer_to_json(trailer_data, args.output)
        else:
            print("\n⚠️  Skipped saving (--no-save flag)")

    except SceneGeneratorError as e:
        print(f"\n❌ Scene generation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
