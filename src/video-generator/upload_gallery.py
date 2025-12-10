#!/usr/bin/env python3
"""
Upload gallery movies and metadata to GCS

This script:
1. Reads all movie JSON files from scene-decomposer/outputs
2. Extracts movie titles and metadata
3. Uploads the trailer video to GCS (using the one available trailer)
4. Creates a gallery manifest file with all movie metadata
5. Uploads the manifest to GCS
"""

import json
import os
from datetime import datetime
from pathlib import Path

from google.cloud import storage

# Configuration
GCS_BUCKET_NAME = "taraintino-showcase-videos"
GCS_PREFIX = "gallery"
SCENE_DECOMPOSER_DIR = Path(__file__).parent.parent / "scene-decomposer" / "outputs"
VIDEO_OUTPUT_DIR = Path(__file__).parent / "output"
TRAILER_VIDEO = VIDEO_OUTPUT_DIR / "trailer_no_audio.mp4"


def extract_movie_metadata(json_path):
    """Extract relevant metadata from a movie JSON file."""
    with open(json_path) as f:
        data = json.load(f)

    # Extract key information
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
    }

    return metadata


def upload_to_gcs(local_path, dest_path, bucket_name, content_type=None):
    """Upload a file to GCS."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dest_path)

    if content_type:
        blob.upload_from_filename(str(local_path), content_type=content_type, timeout=600)
    else:
        blob.upload_from_filename(str(local_path), timeout=600)

    print(f"✓ Uploaded: gs://{bucket_name}/{dest_path}")
    return f"gs://{bucket_name}/{dest_path}"


def main():
    print("=" * 60)
    print("GALLERY UPLOAD SCRIPT")
    print("=" * 60)

    # Step 1: Find all movie JSON files
    print(f"\n[1] Scanning for movie JSON files in: {SCENE_DECOMPOSER_DIR}")
    json_files = list(SCENE_DECOMPOSER_DIR.glob("*_trailer.json"))
    print(f"    Found {len(json_files)} movie files")

    # Step 2: Extract metadata from all movies
    print(f"\n[2] Extracting metadata from {len(json_files)} movies...")
    movies_metadata = []
    for json_file in sorted(json_files):
        try:
            metadata = extract_movie_metadata(json_file)
            movies_metadata.append(metadata)
            print(f"    ✓ {metadata['title']}")
        except Exception as e:
            print(f"    ✗ Error processing {json_file.name}: {e}")

    # Step 3: Check if trailer video exists
    print("\n[3] Checking trailer video...")
    if not TRAILER_VIDEO.exists():
        print(f"    ✗ Trailer video not found: {TRAILER_VIDEO}")
        print("    Please ensure the trailer video exists before running this script.")
        return

    print(f"    ✓ Trailer video found: {TRAILER_VIDEO}")
    print(f"    Size: {TRAILER_VIDEO.stat().st_size / (1024 * 1024):.2f} MB")

    # Step 4: Upload trailer video to GCS
    print("\n[4] Uploading trailer video to GCS...")
    trailer_gcs_path = f"{GCS_PREFIX}/trailers/demo_trailer.mp4"
    try:
        video_url = upload_to_gcs(
            TRAILER_VIDEO, trailer_gcs_path, GCS_BUCKET_NAME, content_type="video/mp4"
        )

        # Add video URL to all movie metadata (they all share the same trailer for demo)
        for movie in movies_metadata:
            movie["video_url"] = video_url
            movie["thumbnail_url"] = video_url  # Could generate actual thumbnails later
    except Exception as e:
        print(f"    ✗ Error uploading video: {e}")
        return

    # Step 5: Create gallery manifest
    print("\n[5] Creating gallery manifest...")
    manifest = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "total_movies": len(movies_metadata),
        "movies": movies_metadata,
    }

    # Save manifest locally
    manifest_path = VIDEO_OUTPUT_DIR / "gallery_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    ✓ Manifest created: {manifest_path}")

    # Step 6: Upload manifest to GCS
    print("\n[6] Uploading manifest to GCS...")
    manifest_gcs_path = f"{GCS_PREFIX}/gallery_manifest.json"
    try:
        upload_to_gcs(
            manifest_path, manifest_gcs_path, GCS_BUCKET_NAME, content_type="application/json"
        )
    except Exception as e:
        print(f"    ✗ Error uploading manifest: {e}")
        return

    # Summary
    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE!")
    print("=" * 60)
    print(f"Movies cataloged: {len(movies_metadata)}")
    print(f"Video URL: {video_url}")
    print(f"Manifest URL: gs://{GCS_BUCKET_NAME}/{manifest_gcs_path}")
    print("\nNext steps:")
    print("1. Create a gallery API endpoint to fetch the manifest")
    print("2. Add a gallery UI component to the quiz page")
    print("=" * 60)


if __name__ == "__main__":
    main()
