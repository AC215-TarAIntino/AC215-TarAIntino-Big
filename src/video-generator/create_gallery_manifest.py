#!/usr/bin/env python3
"""
Create gallery manifest from movie JSON files
"""

import json
import os
from pathlib import Path
from datetime import datetime

SCENE_DECOMPOSER_DIR = Path(__file__).parent.parent / "scene-decomposer" / "outputs"
OUTPUT_DIR = Path(__file__).parent / "output"

def extract_movie_metadata(json_path):
    """Extract relevant metadata from a movie JSON file."""
    with open(json_path, 'r') as f:
        data = json.load(f)

    metadata = {
        "title": data.get("movie_title", "Untitled"),
        "duration": data.get("total_duration", 0),
        "narration": data.get("narration_script", ""),
        "scenes_count": len(data.get("scenes", [])),
        "characters": list(data.get("character_appearance_map", {}).keys()),
        "visual_style": data.get("technical_specs", {}).get("visual_style", ""),
        "aspect_ratio": data.get("technical_specs", {}).get("aspect_ratio", "16:9"),
        "created_at": datetime.fromtimestamp(os.path.getmtime(json_path)).isoformat(),
        "filename": json_path.stem,
        "video_url": "gs://taraintino-showcase-videos/gallery/trailers/demo_trailer.mp4",
        "thumbnail_url": "gs://taraintino-showcase-videos/gallery/trailers/demo_trailer.mp4"
    }

    return metadata

def main():
    print("Creating gallery manifest...")

    json_files = list(SCENE_DECOMPOSER_DIR.glob("*_trailer.json"))
    print(f"Found {len(json_files)} movie files")

    movies_metadata = []
    for json_file in sorted(json_files):
        try:
            metadata = extract_movie_metadata(json_file)
            movies_metadata.append(metadata)
            print(f"  ✓ {metadata['title']}")
        except Exception as e:
            print(f"  ✗ Error processing {json_file.name}: {e}")

    manifest = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "total_movies": len(movies_metadata),
        "movies": movies_metadata
    }

    manifest_path = OUTPUT_DIR / "gallery_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✓ Manifest created: {manifest_path}")
    print(f"✓ Total movies: {len(movies_metadata)}")

if __name__ == "__main__":
    main()
