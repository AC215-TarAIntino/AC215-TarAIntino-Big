"""
Comprehensive tests for app.py FastAPI endpoints.
Tests all API routes and helper functions with proper mocking.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import (
    Scene,
    _build_character_ref_map,
    _collect_referenced_characters,
    _load_default_api_key,
    _resolve_api_key,
    app,
)

# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Test /health endpoint returns ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestLoadDefaultAPIKey:
    """Test _load_default_api_key helper function."""

    def test_load_from_secrets_json(self):
        """Test loading API key from secrets.json."""
        mock_data = {"image_api_key": "test_key_123"}

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=json.dumps(mock_data)),
        ):
            result = _load_default_api_key("image_api_key")

        assert result == "test_key_123"

    def test_load_from_secret_json_fallback(self):
        """Test fallback to secret.json if secrets.json doesn't exist."""
        mock_data = {"image_api_key": "fallback_key"}

        def mock_exists(self):
            # First call (secrets.json) returns False, second call (secret.json) returns True
            if "secrets.json" in str(self):
                return False
            return True

        with (
            patch.object(Path, "exists", mock_exists),
            patch("pathlib.Path.read_text", return_value=json.dumps(mock_data)),
        ):
            result = _load_default_api_key("image_api_key")

        assert result == "fallback_key"

    def test_load_with_project_api_key_fallback(self):
        """Test fallback to project_api_key if requested key not found."""
        mock_data = {"project_api_key": "project_key"}

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=json.dumps(mock_data)),
        ):
            result = _load_default_api_key("image_api_key")

        assert result == "project_key"

    def test_load_no_file_exists(self):
        """Test when no secrets file exists."""
        with patch("pathlib.Path.exists", return_value=False):
            result = _load_default_api_key("image_api_key")

        assert result is None

    def test_load_invalid_json(self):
        """Test handling of invalid JSON in secrets file."""
        import json

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value="invalid json"),
            pytest.raises(json.JSONDecodeError),
        ):
            _load_default_api_key("image_api_key")


class TestResolveAPIKey:
    """Test _resolve_api_key helper function."""

    def test_resolve_with_provided_key(self):
        """Test resolving when key is provided."""
        result = _resolve_api_key("provided_key", "image_api_key")
        assert result == "provided_key"

    @patch("app._load_default_api_key")
    def test_resolve_from_file(self, mock_load):
        """Test resolving from file when key not provided."""
        mock_load.return_value = "file_key"

        result = _resolve_api_key(None, "image_api_key")

        assert result == "file_key"
        mock_load.assert_called_once_with("image_api_key")

    @patch("app._load_default_api_key")
    def test_resolve_missing_key_raises_error(self, mock_load):
        """Test that missing key raises HTTPException."""
        mock_load.return_value = None

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _resolve_api_key(None, "image_api_key")

        assert exc_info.value.status_code == 400
        assert "image_api_key is required" in str(exc_info.value.detail)


class TestCollectReferencedCharacters:
    """Test _collect_referenced_characters helper function."""

    def test_collect_no_characters(self):
        """Test collecting when scenes have no character references."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="establishing",
                duration_seconds=6,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=[],
            )
        ]

        result = _collect_referenced_characters(scenes)
        assert result == []

    def test_collect_single_character(self):
        """Test collecting a single character reference."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="intro",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Character1"],
            )
        ]

        result = _collect_referenced_characters(scenes)
        assert result == ["Character1"]

    def test_collect_multiple_unique_characters(self):
        """Test collecting multiple unique character references."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="intro",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Char1", "Char2"],
            ),
            Scene(
                scene_number=2,
                scene_type="action",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Char3"],
            ),
        ]

        result = _collect_referenced_characters(scenes)
        assert result == ["Char1", "Char2", "Char3"]

    def test_collect_deduplicates_characters(self):
        """Test that duplicate character references are deduplicated."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="intro",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Char1", "Char2"],
            ),
            Scene(
                scene_number=2,
                scene_type="action",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Char1"],  # Duplicate
            ),
        ]

        result = _collect_referenced_characters(scenes)
        assert result == ["Char1", "Char2"]


class TestBuildCharacterRefMap:
    """Test _build_character_ref_map helper function."""

    def test_build_with_provided_refs(self):
        """Test building map when character_refs are provided."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="intro",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Char1"],
            )
        ]

        provided_refs = {"Char1": "/path/to/char1.png"}

        result = _build_character_ref_map(scenes, provided_refs, True)

        assert result == provided_refs

    def test_build_with_missing_provided_refs_raises_error(self):
        """Test that missing provided refs raises HTTPException."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="intro",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Char1", "Char2"],
            )
        ]

        provided_refs = {"Char1": "/path/to/char1.png"}  # Missing Char2

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _build_character_ref_map(scenes, provided_refs, True)

        assert exc_info.value.status_code == 400
        assert "Missing reference paths for: Char2" in str(exc_info.value.detail)

    def test_build_with_autoload_disabled_and_no_refs_raises_error(self):
        """Test that autoload disabled with references raises error."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="intro",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Char1"],
            )
        ]

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            _build_character_ref_map(scenes, None, False)

        assert exc_info.value.status_code == 400
        assert "Reference images required" in str(exc_info.value.detail)

    def test_build_with_autoload_disabled_no_characters_needed(self):
        """Test autoload disabled with no character references works."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="establishing",
                duration_seconds=6,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=[],
            )
        ]

        result = _build_character_ref_map(scenes, None, False)

        assert result == {}

    @patch("app.OUTPUT_DIR", Path("/fake/output"))
    def test_build_with_autoload_success(self):
        """Test autoloading character references from filesystem."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="intro",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Char1"],
            )
        ]

        with patch("pathlib.Path.exists", return_value=True):
            result = _build_character_ref_map(scenes, None, True)

        assert "Char1" in result
        assert "Char1.png" in result["Char1"]

    @patch("app.OUTPUT_DIR", Path("/fake/output"))
    def test_build_with_autoload_missing_file_raises_error(self):
        """Test autoload with missing file raises HTTPException."""
        scenes = [
            Scene(
                scene_number=1,
                scene_type="intro",
                duration_seconds=8,
                start_frame_prompt="Start",
                end_frame_prompt="End",
                video_prompt="Video",
                reference_images=["Char1"],
            )
        ]

        from fastapi import HTTPException

        with (
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(HTTPException) as exc_info,
        ):
            _build_character_ref_map(scenes, None, True)

        assert exc_info.value.status_code == 400
        assert "Reference image not found for 'Char1'" in str(exc_info.value.detail)


class TestCharacterReferencesEndpoint:
    """Test /generate/character-references endpoint."""

    @patch("app.generate_character_references")
    @patch("app._resolve_api_key")
    def test_create_character_references_success(self, mock_resolve_key, mock_gen_chars):
        """Test successful character reference generation."""
        mock_resolve_key.return_value = "fake_key"
        mock_gen_chars.return_value = {"Char1": "/path/to/char1.png"}

        request_data = {
            "character_designs": [
                {
                    "character_name": "Char1",
                    "image_generation_prompt": "A character",
                }
            ]
        }

        response = client.post("/generate/character-references", json=request_data)

        assert response.status_code == 200
        assert response.json() == {"character_refs": {"Char1": "/path/to/char1.png"}}

    @patch("app.generate_character_references")
    @patch("app._resolve_api_key")
    def test_create_character_references_value_error(self, mock_resolve_key, mock_gen_chars):
        """Test handling of ValueError in character generation."""
        mock_resolve_key.return_value = "fake_key"
        mock_gen_chars.side_effect = ValueError("Invalid prompt")

        request_data = {
            "character_designs": [
                {
                    "character_name": "Char1",
                    "image_generation_prompt": "A character",
                }
            ]
        }

        response = client.post("/generate/character-references", json=request_data)

        assert response.status_code == 400
        assert "Invalid prompt" in response.json()["detail"]

    @patch("app._resolve_api_key")
    def test_create_character_references_no_api_key(self, mock_resolve_key):
        """Test error when API key is missing."""
        from fastapi import HTTPException

        mock_resolve_key.side_effect = HTTPException(status_code=400, detail="API key required")

        request_data = {
            "character_designs": [
                {
                    "character_name": "Char1",
                    "image_generation_prompt": "A character",
                }
            ]
        }

        response = client.post("/generate/character-references", json=request_data)

        assert response.status_code == 400


class TestSceneVideosEndpoint:
    """Test /generate/scene-videos endpoint."""

    @patch("app.generate_scene_videos")
    @patch("app._build_character_ref_map")
    @patch("app._resolve_api_key")
    def test_create_scene_videos_success(self, mock_resolve_key, mock_build_refs, mock_gen_videos):
        """Test successful scene video generation."""
        mock_resolve_key.return_value = "fake_key"
        mock_build_refs.return_value = {}
        mock_gen_videos.return_value = [Path("/output/scene_01.mp4")]

        request_data = {
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_type": "establishing",
                    "duration_seconds": 6,
                    "start_frame_prompt": "Start",
                    "end_frame_prompt": "End",
                    "video_prompt": "Video",
                    "reference_images": [],
                }
            ]
        }

        response = client.post("/generate/scene-videos", json=request_data)

        assert response.status_code == 200
        assert len(response.json()["video_paths"]) == 1

    @patch("app.generate_scene_videos")
    @patch("app._build_character_ref_map")
    @patch("app._resolve_api_key")
    def test_create_scene_videos_with_refs(
        self, mock_resolve_key, mock_build_refs, mock_gen_videos
    ):
        """Test scene video generation with character references."""
        mock_resolve_key.return_value = "fake_key"
        mock_build_refs.return_value = {"Char1": "/path/to/char1.png"}
        mock_gen_videos.return_value = [Path("/output/scene_01.mp4")]

        request_data = {
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_type": "intro",
                    "duration_seconds": 8,
                    "start_frame_prompt": "Start",
                    "end_frame_prompt": "End",
                    "video_prompt": "Video",
                    "reference_images": ["Char1"],
                }
            ],
            "character_refs": {"Char1": "/path/to/char1.png"},
        }

        response = client.post("/generate/scene-videos", json=request_data)

        assert response.status_code == 200

    @patch("app.generate_scene_videos")
    @patch("app._build_character_ref_map")
    @patch("app._resolve_api_key")
    def test_create_scene_videos_value_error(
        self, mock_resolve_key, mock_build_refs, mock_gen_videos
    ):
        """Test handling of ValueError in scene generation."""
        mock_resolve_key.return_value = "fake_key"
        mock_build_refs.return_value = {}
        mock_gen_videos.side_effect = ValueError("Invalid scene")

        request_data = {
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_type": "establishing",
                    "duration_seconds": 6,
                    "start_frame_prompt": "Start",
                    "end_frame_prompt": "End",
                    "video_prompt": "Video",
                    "reference_images": [],
                }
            ]
        }

        response = client.post("/generate/scene-videos", json=request_data)

        assert response.status_code == 400
        assert "Invalid scene" in response.json()["detail"]


class TestTrailerGenerationEndpoint:
    """Test /generate/trailer endpoint."""

    @patch("app.stitch_videos")
    @patch("app.generate_scene_videos")
    @patch("app.generate_character_references")
    @patch("app._resolve_api_key")
    def test_generate_trailer_full_success(
        self, mock_resolve_key, mock_gen_chars, mock_gen_videos, mock_stitch
    ):
        """Test full trailer generation with stitching."""
        mock_resolve_key.return_value = "fake_key"
        mock_gen_chars.return_value = {"Char1": "/path/to/char1.png"}
        mock_gen_videos.return_value = [
            Path("/output/scene_01.mp4"),
            Path("/output/scene_02.mp4"),
        ]
        mock_stitch.return_value = Path("/output/trailer_no_audio.mp4")

        request_data = {
            "character_designs": [
                {
                    "character_name": "Char1",
                    "image_generation_prompt": "A character",
                }
            ],
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_type": "intro",
                    "duration_seconds": 8,
                    "start_frame_prompt": "Start",
                    "end_frame_prompt": "End",
                    "video_prompt": "Video",
                    "reference_images": ["Char1"],
                }
            ],
            "stitch_trailer": True,
        }

        response = client.post("/generate/trailer", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "character_refs" in data
        assert "scene_videos" in data
        assert "trailer_path" in data
        assert data["trailer_path"] is not None
        mock_stitch.assert_called_once()

    @patch("app.generate_scene_videos")
    @patch("app.generate_character_references")
    @patch("app._resolve_api_key")
    def test_generate_trailer_no_stitch(self, mock_resolve_key, mock_gen_chars, mock_gen_videos):
        """Test trailer generation without stitching."""
        mock_resolve_key.return_value = "fake_key"
        mock_gen_chars.return_value = {"Char1": "/path/to/char1.png"}
        mock_gen_videos.return_value = [Path("/output/scene_01.mp4")]

        request_data = {
            "character_designs": [
                {
                    "character_name": "Char1",
                    "image_generation_prompt": "A character",
                }
            ],
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_type": "intro",
                    "duration_seconds": 8,
                    "start_frame_prompt": "Start",
                    "end_frame_prompt": "End",
                    "video_prompt": "Video",
                    "reference_images": ["Char1"],
                }
            ],
            "stitch_trailer": False,
        }

        response = client.post("/generate/trailer", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["trailer_path"] is None

    @patch("app.generate_character_references")
    @patch("app._resolve_api_key")
    def test_generate_trailer_value_error(self, mock_resolve_key, mock_gen_chars):
        """Test handling of ValueError in trailer generation."""
        mock_resolve_key.return_value = "fake_key"
        mock_gen_chars.side_effect = ValueError("Invalid character")

        request_data = {
            "character_designs": [
                {
                    "character_name": "Char1",
                    "image_generation_prompt": "A character",
                }
            ],
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_type": "intro",
                    "duration_seconds": 8,
                    "start_frame_prompt": "Start",
                    "end_frame_prompt": "End",
                    "video_prompt": "Video",
                    "reference_images": ["Char1"],
                }
            ],
        }

        response = client.post("/generate/trailer", json=request_data)

        assert response.status_code == 400
        assert "Invalid character" in response.json()["detail"]


class TestMockTrailerEndpoint:
    """Test /generate/trailer/mock endpoint."""

    @patch("app.stitch_videos")
    @patch("app.OUTPUT_DIR", Path("/fake/output"))
    def test_mock_trailer_with_existing_scenes(self, mock_stitch):
        """Test mock trailer generation using existing scenes."""
        mock_stitch.return_value = Path("/fake/output/trailer_no_audio.mp4")

        # Mock existing scene files
        mock_scenes = [
            Path("/fake/output/scenes/scene_01.mp4"),
            Path("/fake/output/scenes/scene_02.mp4"),
        ]

        with patch.object(Path, "glob", return_value=mock_scenes):
            request_data = {
                "character_designs": [
                    {
                        "character_name": "Char1",
                        "image_generation_prompt": "A character",
                    }
                ],
                "scenes": [
                    {
                        "scene_number": 1,
                        "scene_type": "intro",
                        "duration_seconds": 8,
                        "start_frame_prompt": "Start",
                        "end_frame_prompt": "End",
                        "video_prompt": "Video",
                        "reference_images": [],
                    },
                    {
                        "scene_number": 2,
                        "scene_type": "action",
                        "duration_seconds": 8,
                        "start_frame_prompt": "Start",
                        "end_frame_prompt": "End",
                        "video_prompt": "Video",
                        "reference_images": [],
                    },
                ],
                "stitch_trailer": True,
            }

            response = client.post("/generate/trailer/mock", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["character_refs"]) == 1
        assert len(data["scene_videos"]) == 2
        assert data["trailer_path"] is not None

    @patch("app.OUTPUT_DIR", Path("/fake/output"))
    def test_mock_trailer_no_stitch(self):
        """Test mock trailer without stitching."""
        mock_scenes = [Path("/fake/output/scenes/scene_01.mp4")]

        with patch.object(Path, "glob", return_value=mock_scenes):
            request_data = {
                "character_designs": [],
                "scenes": [
                    {
                        "scene_number": 1,
                        "scene_type": "intro",
                        "duration_seconds": 8,
                        "start_frame_prompt": "Start",
                        "end_frame_prompt": "End",
                        "video_prompt": "Video",
                        "reference_images": [],
                    }
                ],
                "stitch_trailer": False,
            }

            response = client.post("/generate/trailer/mock", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["trailer_path"] is None

    @patch("app.OUTPUT_DIR", Path("/fake/output"))
    def test_mock_trailer_no_existing_scenes(self):
        """Test mock trailer when no existing scenes found."""
        with patch.object(Path, "glob", return_value=[]):
            request_data = {
                "character_designs": [],
                "scenes": [
                    {
                        "scene_number": 1,
                        "scene_type": "intro",
                        "duration_seconds": 8,
                        "start_frame_prompt": "Start",
                        "end_frame_prompt": "End",
                        "video_prompt": "Video",
                        "reference_images": [],
                    }
                ],
                "stitch_trailer": False,
            }

            response = client.post("/generate/trailer/mock", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["scene_videos"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
