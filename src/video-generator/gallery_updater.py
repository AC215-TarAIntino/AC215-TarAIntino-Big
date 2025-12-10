#!/usr/bin/env python3
"""
Gallery manifest updater - automatically adds newly generated trailers to the gallery.
"""

import json
from datetime import datetime
from pathlib import Path

from google.cloud import storage


class GalleryUpdater:
    """Updates the gallery manifest when new trailers are generated."""

    def __init__(
        self,
        bucket_name: str = "taraintino-showcase-videos",
        manifest_path: str = "gallery/gallery_manifest.json",
    ):
        self.bucket_name = bucket_name
        self.manifest_path = manifest_path
        self.client = storage.Client()

    def fetch_manifest(self) -> dict:
        """Fetch the current gallery manifest from GCS."""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(self.manifest_path)
            manifest_bytes = blob.download_as_bytes()
            return json.loads(manifest_bytes.decode("utf-8"))
        except Exception as e:
            print(f"⚠️  Could not fetch manifest (creating new): {e}")
            # Return empty manifest structure if not found
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "total_movies": 0,
                "movies": [],
            }

    def add_trailer_to_manifest(
        self,
        title: str,
        video_url: str,
        screenplay_data: dict | None = None,
        duration: int = 16,
    ) -> dict:
        """
        Add a newly generated trailer to the gallery manifest.

        Args:
            title: Movie title
            video_url: GCS URL to the video (gs://bucket/path/to/video.mp4)
            screenplay_data: Optional screenplay JSON data containing metadata
            duration: Video duration in seconds

        Returns:
            Updated manifest dictionary
        """
        manifest = self.fetch_manifest()

        # Extract metadata from screenplay if provided
        narration = ""
        characters = []
        scenes_count = 0
        visual_style = "hyper-realistic"

        if screenplay_data:
            # Handle both full screenplay structure and trailer structure
            narration = (
                screenplay_data.get("narration_script", "") or
                screenplay_data.get("narration", "") or
                screenplay_data.get("synopsis", "")
            )

            # Extract characters from either character_appearance_map or character_designs
            char_map = screenplay_data.get("character_appearance_map", {})
            char_designs = screenplay_data.get("character_designs", {})
            characters = list(char_map.keys()) if char_map else list(char_designs.keys())

            scenes_count = len(screenplay_data.get("scenes", []))

            technical_specs = screenplay_data.get("technical_specs", {})
            visual_style = technical_specs.get("visual_style", "hyper-realistic")

        # Create new movie entry
        new_movie = {
            "title": title,
            "duration": duration,
            "narration": narration,
            "scenes_count": scenes_count,
            "characters": characters,
            "visual_style": visual_style,
            "aspect_ratio": "16:9",
            "created_at": datetime.now().isoformat(),
            "filename": Path(video_url).stem,
            "video_url": video_url,
            "thumbnail_url": video_url,  # Use video URL as thumbnail (can be improved)
        }

        # Check if movie already exists (by title)
        existing_titles = [m["title"] for m in manifest["movies"]]
        if title in existing_titles:
            print(f"⚠️  Movie '{title}' already exists in gallery, updating...")
            # Update existing entry
            for i, movie in enumerate(manifest["movies"]):
                if movie["title"] == title:
                    manifest["movies"][i] = new_movie
                    break
        else:
            # Add new entry
            manifest["movies"].append(new_movie)
            manifest["total_movies"] = len(manifest["movies"])
            print(f"✓ Added '{title}' to gallery manifest")

        # Update manifest metadata
        manifest["created_at"] = datetime.now().isoformat()

        return manifest

    def upload_manifest(self, manifest: dict) -> None:
        """Upload the updated manifest back to GCS."""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(self.manifest_path)

            # Upload with public read access
            blob.upload_from_string(
                json.dumps(manifest, indent=2),
                content_type="application/json",
            )

            # Make it public so frontend can fetch it
            try:
                blob.make_public()
                print(f"✓ Updated gallery manifest at gs://{self.bucket_name}/{self.manifest_path}")
            except Exception as e:
                print(f"⚠️  Manifest uploaded but could not make public: {e}")

        except Exception as e:
            print(f"❌ Failed to upload manifest: {e}")
            raise

    def add_and_upload(
        self,
        title: str,
        video_url: str,
        screenplay_data: dict | None = None,
        duration: int = 16,
    ) -> None:
        """
        Convenience method: add trailer to manifest and upload in one step.

        Args:
            title: Movie title
            video_url: GCS URL to the video
            screenplay_data: Optional screenplay JSON data
            duration: Video duration in seconds
        """
        manifest = self.add_trailer_to_manifest(title, video_url, screenplay_data, duration)
        self.upload_manifest(manifest)


def update_gallery_with_trailer(
    title: str,
    video_url: str,
    screenplay_data: dict | None = None,
    duration: int = 16,
) -> None:
    """
    Standalone function to update gallery with a newly generated trailer.

    Args:
        title: Movie title
        video_url: GCS URL to the video (gs://bucket/path/to/video.mp4)
        screenplay_data: Optional screenplay JSON data containing metadata
        duration: Video duration in seconds
    """
    updater = GalleryUpdater()
    updater.add_and_upload(title, video_url, screenplay_data, duration)
    print(f"🎬 Gallery updated with '{title}'")
