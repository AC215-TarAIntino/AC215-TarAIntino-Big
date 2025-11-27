"""
Comprehensive tests for generate.py module.
Tests all video generation functions with proper mocking.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate import (
    GCS_BUCKET_NAME,
    GCS_PREFIX,
    generate_character_references,
    generate_image,
    generate_scene_videos,
    generate_video_veo,
    stitch_videos,
    upload_to_gcs,
)


class TestUploadToGCS:
    """Test GCS upload functionality."""

    @patch("generate.storage.Client")
    def test_upload_to_gcs_with_prefix(self, mock_storage_client):
        """Test uploading a file to GCS with prefix."""
        # Setup mocks
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        local_path = Path("output/test.png")
        dest_path = "refs/test.png"

        # Execute
        upload_to_gcs(local_path, dest_path)

        # Verify
        mock_client.bucket.assert_called_once_with(GCS_BUCKET_NAME)
        mock_bucket.blob.assert_called_once_with(f"{GCS_PREFIX}/{dest_path}")
        mock_blob.upload_from_filename.assert_called_once_with(str(local_path))

    @patch("generate.storage.Client")
    def test_upload_to_gcs_without_prefix(self, mock_storage_client):
        """Test uploading when GCS_PREFIX is empty."""
        # Setup mocks
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        local_path = Path("output/test.png")
        dest_path = "refs/test.png"

        # Temporarily patch GCS_PREFIX
        with patch("generate.GCS_PREFIX", ""):
            upload_to_gcs(local_path, dest_path)

        # Verify blob is called with dest_path directly
        mock_bucket.blob.assert_called_once_with(dest_path)


class TestGenerateImage:
    """Test image generation functionality."""

    @patch("generate.genai.Client")
    def test_generate_image_success(self, mock_genai_client):
        """Test successful image generation."""
        # Setup mock response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_inline_data = MagicMock()

        # Setup the response structure
        mock_inline_data.data = b"fake_image_data"
        mock_part.text = None
        mock_part.inline_data = mock_inline_data
        mock_candidate.content.parts = [mock_part]
        mock_response.candidates = [mock_candidate]

        mock_client.models.generate_content.return_value = mock_response
        mock_genai_client.return_value = mock_client

        # Execute
        result = generate_image("fake_api_key", "test prompt")

        # Verify
        assert result == b"fake_image_data"
        mock_genai_client.assert_called_once_with(api_key="fake_api_key")
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash-image", contents=["test prompt"]
        )

    @patch("generate.genai.Client")
    def test_generate_image_with_text_response(self, mock_genai_client):
        """Test image generation when response contains text."""
        # Setup mock response with text part
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_part1 = MagicMock()
        mock_part2 = MagicMock()
        mock_inline_data = MagicMock()

        # First part has text, second has image
        mock_part1.text = "Some text response"
        mock_inline_data.data = b"fake_image_data"
        mock_part2.text = None
        mock_part2.inline_data = mock_inline_data

        mock_candidate.content.parts = [mock_part1, mock_part2]
        mock_response.candidates = [mock_candidate]

        mock_client.models.generate_content.return_value = mock_response
        mock_genai_client.return_value = mock_client

        # Execute
        result = generate_image("fake_api_key", "test prompt")

        # Verify - should skip text and return image
        assert result == b"fake_image_data"

    @patch("generate.genai.Client")
    def test_generate_image_no_image_data(self, mock_genai_client):
        """Test image generation when no image data is found."""
        # Setup mock response with no image data
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_part = MagicMock()

        mock_part.text = "Just text"
        mock_part.inline_data = None
        mock_candidate.content.parts = [mock_part]
        mock_response.candidates = [mock_candidate]

        mock_client.models.generate_content.return_value = mock_response
        mock_genai_client.return_value = mock_client

        # Execute and verify exception
        with pytest.raises(ValueError, match="No image data found in response"):
            generate_image("fake_api_key", "test prompt")

    @patch("generate.genai.Client")
    def test_generate_image_no_candidates(self, mock_genai_client):
        """Test image generation when response has no candidates."""
        # Setup mock response with no candidates
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = []

        mock_client.models.generate_content.return_value = mock_response
        mock_genai_client.return_value = mock_client

        # Execute and verify exception
        with pytest.raises(ValueError, match="No image data found in response"):
            generate_image("fake_api_key", "test prompt")


class TestGenerateVideoVEO:
    """Test VEO video generation functionality."""

    @patch("generate.genai.Client")
    @patch("generate.time.sleep")
    def test_generate_video_veo_success_no_refs(self, mock_sleep, mock_genai_client):
        """Test successful video generation without reference images."""
        # Setup mocks
        mock_client = MagicMock()
        mock_operation = MagicMock()
        mock_video = MagicMock()
        mock_video_file = MagicMock()

        # First call: operation not done, second call: done
        mock_operation.done = False
        mock_done_operation = MagicMock()
        mock_done_operation.done = True
        mock_done_operation.response.generated_videos = [mock_video]
        # Fix: Set up the mock correctly - configure read() on mock_video_file first
        mock_video_file.read.return_value = b"fake_video_data"
        mock_video.video = mock_video_file

        mock_client.models.generate_videos.return_value = mock_operation
        mock_client.operations.get.return_value = mock_done_operation
        mock_genai_client.return_value = mock_client

        # Execute
        result = generate_video_veo(
            veo_api_key="fake_key",
            prompt="test video prompt",
            start_frame=b"start_image",
            end_frame=b"end_image",
            duration=6,
            reference_images=[],
        )

        # Verify
        assert result == b"fake_video_data"
        mock_client.models.generate_videos.assert_called_once()
        mock_client.operations.get.assert_called_once()
        mock_sleep.assert_called()

    @patch("generate.genai.Client")
    def test_generate_video_veo_with_references(self, mock_genai_client):
        """Test video generation with reference images."""
        # Setup mocks
        mock_client = MagicMock()
        mock_operation = MagicMock()
        mock_video = MagicMock()

        mock_operation.done = True
        mock_operation.response.generated_videos = [mock_video]
        mock_video.video.read.return_value = b"fake_video_data"

        mock_client.models.generate_videos.return_value = mock_operation
        mock_genai_client.return_value = mock_client

        # Execute with exactly 8 seconds (required for references)
        result = generate_video_veo(
            veo_api_key="fake_key",
            prompt="test video prompt",
            start_frame=b"start_image",
            end_frame=b"end_image",
            duration=8,
            reference_images=[b"ref1", b"ref2"],
        )

        # Verify
        assert result == b"fake_video_data"

    def test_generate_video_veo_invalid_duration_with_refs(self):
        """Test that non-8s duration with references raises ValueError."""
        with pytest.raises(ValueError, match="Duration must be 8s when using reference images"):
            generate_video_veo(
                veo_api_key="fake_key",
                prompt="test prompt",
                start_frame=b"start",
                end_frame=b"end",
                duration=6,  # Invalid - must be 8s with references
                reference_images=[b"ref1"],
            )

    def test_generate_video_veo_too_many_refs(self):
        """Test that more than 3 reference images raises ValueError."""
        with pytest.raises(ValueError, match="Max 3 reference images allowed"):
            generate_video_veo(
                veo_api_key="fake_key",
                prompt="test prompt",
                start_frame=b"start",
                end_frame=b"end",
                duration=8,
                reference_images=[b"ref1", b"ref2", b"ref3", b"ref4"],  # Too many
            )


class TestGenerateCharacterReferences:
    """Test character reference generation."""

    @patch("generate.upload_to_gcs")
    @patch("generate.generate_image")
    @patch("generate.OUTPUT_DIR", Path("/fake/output"))
    def test_generate_character_references_single(self, mock_gen_image, mock_upload_gcs):
        """Test generating a single character reference."""
        # Setup
        mock_gen_image.return_value = b"fake_image_data"

        character_designs = [
            {
                "character_name": "TestChar",
                "image_generation_prompt": "A test character",
            }
        ]

        # Mock Path operations
        with patch("generate.Path.mkdir"), patch("generate.Path.write_bytes"):

            result = generate_character_references("fake_key", character_designs)

        # Verify
        assert "TestChar" in result
        assert "TestChar.png" in result["TestChar"]
        mock_gen_image.assert_called_once_with("fake_key", "A test character")
        mock_upload_gcs.assert_called_once()

    @patch("generate.upload_to_gcs")
    @patch("generate.generate_image")
    @patch("generate.OUTPUT_DIR", Path("/fake/output"))
    def test_generate_character_references_multiple(self, mock_gen_image, mock_upload_gcs):
        """Test generating multiple character references."""
        # Setup
        mock_gen_image.return_value = b"fake_image_data"

        character_designs = [
            {"character_name": "Char1", "image_generation_prompt": "Character 1"},
            {"character_name": "Char2", "image_generation_prompt": "Character 2"},
            {"character_name": "Char3", "image_generation_prompt": "Character 3"},
        ]

        # Mock Path operations
        with patch("generate.Path.mkdir"), patch("generate.Path.write_bytes"):

            result = generate_character_references("fake_key", character_designs)

        # Verify
        assert len(result) == 3
        assert "Char1" in result
        assert "Char2" in result
        assert "Char3" in result
        assert mock_gen_image.call_count == 3
        assert mock_upload_gcs.call_count == 3


class TestGenerateSceneVideos:
    """Test scene video generation."""

    @patch("generate.upload_to_gcs")
    @patch("generate.generate_video_veo")
    @patch("generate.generate_image")
    @patch("generate.OUTPUT_DIR", Path("/fake/output"))
    def test_generate_scene_videos_no_refs(self, mock_gen_image, mock_gen_video, mock_upload_gcs):
        """Test generating scene videos without character references."""
        # Setup
        mock_gen_image.return_value = b"fake_image_data"
        mock_gen_video.return_value = b"fake_video_data"

        scenes = [
            {
                "scene_number": 1,
                "scene_type": "establishing",
                "duration_seconds": 6,
                "start_frame_prompt": "Start frame",
                "end_frame_prompt": "End frame",
                "video_prompt": "Video prompt",
                "reference_images": [],
            }
        ]

        # Mock Path operations
        with patch("generate.Path.mkdir"), patch("generate.Path.write_bytes"):

            result = generate_scene_videos("img_key", "veo_key", scenes, {})

        # Verify
        assert len(result) == 1
        assert "scene_01.mp4" in str(result[0])
        assert mock_gen_image.call_count == 2  # start and end frames
        mock_gen_video.assert_called_once()

    @patch("generate.upload_to_gcs")
    @patch("generate.generate_video_veo")
    @patch("generate.generate_image")
    @patch("generate.OUTPUT_DIR", Path("/fake/output"))
    def test_generate_scene_videos_with_refs(self, mock_gen_image, mock_gen_video, mock_upload_gcs):
        """Test generating scene videos with character references."""
        # Setup
        mock_gen_image.return_value = b"fake_image_data"
        mock_gen_video.return_value = b"fake_video_data"

        scenes = [
            {
                "scene_number": 1,
                "scene_type": "character_intro",
                "duration_seconds": 8,
                "start_frame_prompt": "Start frame",
                "end_frame_prompt": "End frame",
                "video_prompt": "Video prompt",
                "reference_images": ["Char1", "Char2"],
            }
        ]

        character_refs = {
            "Char1": "/fake/output/refs/Char1.png",
            "Char2": "/fake/output/refs/Char2.png",
        }

        # Mock Path operations
        with (
            patch("generate.Path.mkdir"),
            patch("generate.Path.write_bytes"),
            patch("generate.Path.read_bytes", return_value=b"ref_image_data"),
        ):

            result = generate_scene_videos("img_key", "veo_key", scenes, character_refs)

        # Verify
        assert len(result) == 1
        mock_gen_video.assert_called_once()
        # Check that reference images were passed
        call_args = mock_gen_video.call_args
        assert len(call_args.kwargs["reference_images"]) == 2

    @patch("generate.upload_to_gcs")
    @patch("generate.generate_video_veo")
    @patch("generate.generate_image")
    @patch("generate.OUTPUT_DIR", Path("/fake/output"))
    def test_generate_scene_videos_multiple_scenes(
        self, mock_gen_image, mock_gen_video, mock_upload_gcs
    ):
        """Test generating multiple scene videos."""
        # Setup
        mock_gen_image.return_value = b"fake_image_data"
        mock_gen_video.return_value = b"fake_video_data"

        scenes = [
            {
                "scene_number": 1,
                "scene_type": "establishing",
                "duration_seconds": 6,
                "start_frame_prompt": "Start 1",
                "end_frame_prompt": "End 1",
                "video_prompt": "Video 1",
                "reference_images": [],
            },
            {
                "scene_number": 2,
                "scene_type": "action",
                "duration_seconds": 6,
                "start_frame_prompt": "Start 2",
                "end_frame_prompt": "End 2",
                "video_prompt": "Video 2",
                "reference_images": [],
            },
        ]

        # Mock Path operations
        with patch("generate.Path.mkdir"), patch("generate.Path.write_bytes"):

            result = generate_scene_videos("img_key", "veo_key", scenes, {})

        # Verify
        assert len(result) == 2
        assert mock_gen_image.call_count == 4  # 2 scenes * 2 frames each
        assert mock_gen_video.call_count == 2


class TestStitchVideos:
    """Test video stitching functionality."""

    @patch("generate.upload_to_gcs")
    @patch("subprocess.run")
    @patch("generate.OUTPUT_DIR", Path("/fake/output"))
    def test_stitch_videos_success(self, mock_subprocess, mock_upload_gcs):
        """Test successfully stitching videos together."""
        # Setup
        video_paths = [
            Path("/fake/output/scenes/scene_01.mp4"),
            Path("/fake/output/scenes/scene_02.mp4"),
            Path("/fake/output/scenes/scene_03.mp4"),
        ]

        # Mock file writing
        with patch("builtins.open", mock_open()) as mock_file:
            result = stitch_videos(video_paths)

        # Verify concat file was written
        mock_file.assert_called()

        # Verify ffmpeg was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "ffmpeg" in call_args
        assert "-f" in call_args
        assert "concat" in call_args

        # Verify result path
        assert "trailer_no_audio.mp4" in str(result)
        mock_upload_gcs.assert_called_once()

    @patch("generate.upload_to_gcs")
    @patch("subprocess.run")
    @patch("generate.OUTPUT_DIR", Path("/fake/output"))
    def test_stitch_videos_single_video(self, mock_subprocess, mock_upload_gcs):
        """Test stitching a single video."""
        video_paths = [Path("/fake/output/scenes/scene_01.mp4")]

        with patch("builtins.open", mock_open()):
            result = stitch_videos(video_paths)

        # Should still call ffmpeg
        mock_subprocess.assert_called_once()
        assert "trailer_no_audio.mp4" in str(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
