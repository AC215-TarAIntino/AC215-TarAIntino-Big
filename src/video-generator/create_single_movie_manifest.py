#!/usr/bin/env python3
"""
Create gallery manifest with only the single movie that has an actual video
"""

import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "output"
SCENE_DECOMPOSER_DIR = Path(__file__).parent.parent / "scene-decomposer" / "outputs"

# Use Demon's Melody as our showcase movie
MOVIE_JSON = SCENE_DECOMPOSER_DIR / "demon's_melody_trailer.json"

def main():
    print("Creating single-movie gallery manifest...")

    # Load the movie data
    with open(MOVIE_JSON, 'r') as f:
        movie_data = json.load(f)

    # Create manifest with just this one movie
    manifest = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "total_movies": 1,
        "movies": [{
            "title": movie_data.get("movie_title", "Demon's Melody"),
            "duration": movie_data.get("total_duration", 16),
            "narration": movie_data.get("narration_script", ""),
            "scenes_count": len(movie_data.get("scenes", [])),
            "characters": list(movie_data.get("character_appearance_map", {}).keys()),
            "visual_style": movie_data.get("technical_specs", {}).get("visual_style", "hyper-realistic"),
            "aspect_ratio": movie_data.get("technical_specs", {}).get("aspect_ratio", "16:9"),
            "created_at": datetime.now().isoformat(),
            "filename": "demon's_melody_trailer",
            "video_url": "gs://taraintino-showcase-videos/gallery/trailers/demo_trailer.mp4",
            "thumbnail_url": "gs://taraintino-showcase-videos/gallery/trailers/demo_trailer.mp4"
        }]
    }

    # Save manifest
    manifest_path = OUTPUT_DIR / "gallery_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✓ Single-movie manifest created: {manifest_path}")
    print(f"✓ Movie: {manifest['movies'][0]['title']}")
    print(f"✓ Characters: {', '.join(manifest['movies'][0]['characters'])}")

if __name__ == "__main__":
    main()
