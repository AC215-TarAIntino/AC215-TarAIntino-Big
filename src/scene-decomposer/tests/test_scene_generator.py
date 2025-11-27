"""
Comprehensive tests for scene_generator.py - SceneGenerator class.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trailer_generator.scene_generator import SceneGenerator, SceneGeneratorError
from trailer_generator.schemas import (
    CastMember,
    CharacterDesign,
    GeneratedMovie,
    TechnicalSpecs,
    TrailerBreakdown,
    TrailerScene,
)


@pytest.fixture
def sample_movie():
    """Create a sample movie for testing."""
    return GeneratedMovie(
        title="Test Movie",
        tagline="Test tagline",
        genres=["Sci-Fi", "Thriller"],
        plot_summary="A scientist discovers something amazing and must save the world.",
        director_name="Test Director",
        director_background="Acclaimed director",
        writers=["Writer One"],
        writer_backgrounds="Experienced writer",
        cast=[
            CastMember(
                actor_name="Actor One",
                character_name="Character One",
                physical_description="Tall person with dark hair",
                personality_traits=["brave", "smart"],
                acting_style="intense",
                role_description="Hero",
            )
        ],
        runtime="120 minutes",
        rating="PG-13",
        release_year=2024,
        production_company="Test Studios",
        production_company_background="Major studio",
        budget="$100M",
        themes=["science", "survival"],
        visual_style="Dark and moody",
        target_audience="Adults",
    )


@pytest.fixture
def sample_trailer_data():
    """Create sample trailer breakdown data."""
    return {
        "movie_title": "Test Movie",
        "total_duration": 30,
        "character_designs": [
            {
                "character_name": "Character_One",
                "image_generation_prompt": "A tall person with dark hair standing on a pure white background. Hyper-realistic style.",
                "brief_identifier": "tall person, dark hair",
                "visual_style": "hyper-realistic",
            }
        ],
        "scenes": [
            {
                "scene_number": 1,
                "duration_seconds": 8,
                "scene_type": "establishing",
                "start_frame_prompt": "Wide shot of a laboratory",
                "end_frame_prompt": "Close up of equipment",
                "video_prompt": "Camera pans across laboratory",
                "reference_images": ["Character_One"],
                "characters_present": ["Character One"],
            },
            {
                "scene_number": 2,
                "duration_seconds": 6,
                "scene_type": "action",
                "start_frame_prompt": "Character running",
                "end_frame_prompt": "Character stopping",
                "video_prompt": "Fast-paced action sequence",
                "reference_images": [],
                "characters_present": [],
            },
        ],
        "narration_script": "In a world of science...",
        "continuity_guide": "Maintain dark atmosphere",
        "technical_specs": {
            "color_grading": "Dark and moody",
            "aspect_ratio": "16:9",
            "visual_style": "Cinematic",
            "sound_design_notes": "Suspenseful music",
        },
        "character_appearance_map": {"Character One": [1]},
    }


class TestSceneGenerator:
    """Tests for the SceneGenerator class."""

    def test_initialization_default(self):
        """Test SceneGenerator initializes with default settings."""
        with patch("trailer_generator.scene_generator.settings") as mock_settings:
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.openrouter_model = "test-model"
            mock_settings.openrouter_base_url = "https://test-url.com"

            generator = SceneGenerator()

            assert generator.api_key == "test-key"
            assert generator.model == "test-model"
            assert generator.base_url == "https://test-url.com"

    def test_initialization_custom(self):
        """Test SceneGenerator initializes with custom parameters."""
        generator = SceneGenerator(
            api_key="custom-key", model="custom-model", base_url="https://custom-url.com"
        )

        assert generator.api_key == "custom-key"
        assert generator.model == "custom-model"
        assert generator.base_url == "https://custom-url.com"

    def test_create_generation_prompt(self, sample_movie):
        """Test that generation prompt is created correctly."""
        generator = SceneGenerator(api_key="test-key")
        prompt = generator._create_generation_prompt(
            movie=sample_movie, target_duration=35, include_narration=True
        )

        # Check key sections are included
        assert sample_movie.title in prompt
        assert sample_movie.tagline in prompt
        assert "CHARACTER DESIGNS" in prompt
        assert "SCENE GENERATION" in prompt
        assert "narration_script" in prompt
        assert "technical_specs" in prompt

    def test_create_generation_prompt_without_narration(self, sample_movie):
        """Test prompt creation without narration."""
        generator = SceneGenerator(api_key="test-key")
        prompt = generator._create_generation_prompt(
            movie=sample_movie, target_duration=35, include_narration=False
        )

        assert "narration_script" not in prompt

    def test_create_generation_prompt_different_durations(self, sample_movie):
        """Test prompt creation with different target durations."""
        generator = SceneGenerator(api_key="test-key")

        # Currently all durations get 2 scenes due to quota management
        for duration in [25, 35, 45, 60]:
            prompt = generator._create_generation_prompt(
                movie=sample_movie, target_duration=duration, include_narration=True
            )
            assert f"~{duration} seconds" in prompt or f"{duration}-second" in prompt

    @patch("trailer_generator.scene_generator.OpenAI")
    def test_generate_trailer_success(self, mock_openai_class, sample_movie, sample_trailer_data):
        """Test successful trailer generation."""
        # Mock the OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(sample_trailer_data)

        mock_client.chat.completions.create.return_value = mock_response

        # Generate trailer
        generator = SceneGenerator(api_key="test-key")
        trailer = generator.generate_trailer(
            movie=sample_movie, target_duration=30, include_narration=True
        )

        # Verify result
        assert isinstance(trailer, TrailerBreakdown)
        assert trailer.movie_title == "Test Movie"
        assert trailer.total_duration == 30
        assert len(trailer.scenes) == 2
        assert len(trailer.character_designs) == 1

    @patch("trailer_generator.scene_generator.OpenAI")
    def test_generate_trailer_with_model_override(
        self, mock_openai_class, sample_movie, sample_trailer_data
    ):
        """Test trailer generation with model override."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(sample_trailer_data)
        mock_client.chat.completions.create.return_value = mock_response

        generator = SceneGenerator(api_key="test-key", model="default-model")
        generator.generate_trailer(
            movie=sample_movie, target_duration=30, model_override="override-model"
        )

        # Verify the override model was used
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "override-model"

    @patch("trailer_generator.scene_generator.OpenAI")
    def test_generate_trailer_empty_response(self, mock_openai_class, sample_movie):
        """Test handling of empty LLM response."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None

        mock_client.chat.completions.create.return_value = mock_response

        generator = SceneGenerator(api_key="test-key")

        with pytest.raises(SceneGeneratorError, match="Empty response from LLM"):
            generator.generate_trailer(movie=sample_movie)

    @patch("trailer_generator.scene_generator.OpenAI")
    def test_generate_trailer_invalid_json(self, mock_openai_class, sample_movie):
        """Test handling of invalid JSON response."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not valid JSON"

        mock_client.chat.completions.create.return_value = mock_response

        generator = SceneGenerator(api_key="test-key")

        with pytest.raises(SceneGeneratorError, match="Failed to parse LLM response as JSON"):
            generator.generate_trailer(movie=sample_movie)

    @patch("trailer_generator.scene_generator.OpenAI")
    def test_generate_trailer_json_with_extra_text(
        self, mock_openai_class, sample_movie, sample_trailer_data
    ):
        """Test handling of JSON with surrounding text."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Add extra text before and after JSON
        json_content = json.dumps(sample_trailer_data)
        content_with_extra = f"Here's the trailer:\n\n{json_content}\n\nHope this helps!"

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = content_with_extra

        mock_client.chat.completions.create.return_value = mock_response

        generator = SceneGenerator(api_key="test-key")
        trailer = generator.generate_trailer(movie=sample_movie)

        # Should successfully extract JSON and parse
        assert isinstance(trailer, TrailerBreakdown)

    @patch("trailer_generator.scene_generator.OpenAI")
    def test_generate_trailer_api_error(self, mock_openai_class, sample_movie):
        """Test handling of API errors."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_client.chat.completions.create.side_effect = Exception("API Error")

        generator = SceneGenerator(api_key="test-key")

        with pytest.raises(SceneGeneratorError, match="Failed to generate trailer"):
            generator.generate_trailer(movie=sample_movie)

    def test_build_character_appearance_map(self):
        """Test building character appearance map."""
        scenes = [
            TrailerScene(
                scene_number=1,
                duration_seconds=8,
                scene_type="test",
                start_frame_prompt="test",
                end_frame_prompt="test",
                video_prompt="test",
                reference_images=[],
                characters_present=["Character A", "Character B"],
            ),
            TrailerScene(
                scene_number=2,
                duration_seconds=8,
                scene_type="test",
                start_frame_prompt="test",
                end_frame_prompt="test",
                video_prompt="test",
                reference_images=[],
                characters_present=["Character A"],
            ),
            TrailerScene(
                scene_number=3,
                duration_seconds=6,
                scene_type="test",
                start_frame_prompt="test",
                end_frame_prompt="test",
                video_prompt="test",
                reference_images=[],
                characters_present=["Character C"],
            ),
        ]

        generator = SceneGenerator(api_key="test-key")
        char_map = generator._build_character_appearance_map(scenes)

        assert char_map["Character A"] == [1, 2]
        assert char_map["Character B"] == [1]
        assert char_map["Character C"] == [3]

    def test_validate_trailer_consistency_valid(self):
        """Test validation of a valid trailer breakdown."""
        trailer = TrailerBreakdown(
            movie_title="Test",
            total_duration=30,
            character_designs=[
                CharacterDesign(
                    character_name="Char_One",
                    image_generation_prompt="test prompt",
                    brief_identifier="test",
                    visual_style="realistic",
                )
            ],
            scenes=[
                TrailerScene(
                    scene_number=1,
                    duration_seconds=8,
                    scene_type="test",
                    start_frame_prompt="test",
                    end_frame_prompt="test",
                    video_prompt="test",
                    reference_images=["Char_One"],
                    characters_present=["Char One"],
                )
            ],
            technical_specs=TechnicalSpecs(
                color_grading="test",
                aspect_ratio="16:9",
                visual_style="test",
                sound_design_notes="test",
            ),
            character_appearance_map={"Char One": [1]},
        )

        generator = SceneGenerator(api_key="test-key")
        # Should not raise any exception
        generator._validate_trailer_consistency(trailer)

    def test_validate_trailer_consistency_wrong_duration(self):
        """Test validation fails when reference_images used but duration != 8."""
        trailer = TrailerBreakdown(
            movie_title="Test",
            total_duration=30,
            character_designs=[
                CharacterDesign(
                    character_name="Char_One",
                    image_generation_prompt="test",
                    brief_identifier="test",
                    visual_style="realistic",
                )
            ],
            scenes=[
                TrailerScene(
                    scene_number=1,
                    duration_seconds=6,  # Wrong! Should be 8 when using reference_images
                    scene_type="test",
                    start_frame_prompt="test",
                    end_frame_prompt="test",
                    video_prompt="test",
                    reference_images=["Char_One"],
                    characters_present=["Char One"],
                )
            ],
            technical_specs=TechnicalSpecs(
                color_grading="test",
                aspect_ratio="16:9",
                visual_style="test",
                sound_design_notes="test",
            ),
            character_appearance_map={"Char One": [1]},
        )

        generator = SceneGenerator(api_key="test-key")

        with pytest.raises(SceneGeneratorError, match="exactly 8 seconds"):
            generator._validate_trailer_consistency(trailer)

    def test_validate_trailer_consistency_too_many_references(self):
        """Test validation fails when more than 3 reference images."""
        trailer = TrailerBreakdown(
            movie_title="Test",
            total_duration=30,
            character_designs=[
                CharacterDesign(
                    character_name=f"Char_{i}",
                    image_generation_prompt="test",
                    brief_identifier="test",
                    visual_style="realistic",
                )
                for i in range(4)
            ],
            scenes=[
                TrailerScene(
                    scene_number=1,
                    duration_seconds=8,
                    scene_type="test",
                    start_frame_prompt="test",
                    end_frame_prompt="test",
                    video_prompt="test",
                    reference_images=["Char_0", "Char_1", "Char_2", "Char_3"],  # Too many!
                    characters_present=[],
                )
            ],
            technical_specs=TechnicalSpecs(
                color_grading="test",
                aspect_ratio="16:9",
                visual_style="test",
                sound_design_notes="test",
            ),
            character_appearance_map={},
        )

        generator = SceneGenerator(api_key="test-key")

        with pytest.raises(SceneGeneratorError, match="maximum 3 reference images"):
            generator._validate_trailer_consistency(trailer)

    def test_validate_trailer_consistency_missing_character(self):
        """Test validation fails when referencing non-existent character."""
        trailer = TrailerBreakdown(
            movie_title="Test",
            total_duration=30,
            character_designs=[
                CharacterDesign(
                    character_name="Char_One",
                    image_generation_prompt="test",
                    brief_identifier="test",
                    visual_style="realistic",
                )
            ],
            scenes=[
                TrailerScene(
                    scene_number=1,
                    duration_seconds=8,
                    scene_type="test",
                    start_frame_prompt="test",
                    end_frame_prompt="test",
                    video_prompt="test",
                    reference_images=["Char_Two"],  # Doesn't exist!
                    characters_present=[],
                )
            ],
            technical_specs=TechnicalSpecs(
                color_grading="test",
                aspect_ratio="16:9",
                visual_style="test",
                sound_design_notes="test",
            ),
            character_appearance_map={},
        )

        generator = SceneGenerator(api_key="test-key")

        with pytest.raises(SceneGeneratorError, match="not in character_designs"):
            generator._validate_trailer_consistency(trailer)

    def test_validate_trailer_consistency_empty_reference_images(self):
        """Test validation passes with empty reference_images and any duration."""
        trailer = TrailerBreakdown(
            movie_title="Test",
            total_duration=30,
            character_designs=[],
            scenes=[
                TrailerScene(
                    scene_number=1,
                    duration_seconds=6,  # OK because no reference images
                    scene_type="test",
                    start_frame_prompt="test",
                    end_frame_prompt="test",
                    video_prompt="test",
                    reference_images=[],
                    characters_present=[],
                )
            ],
            technical_specs=TechnicalSpecs(
                color_grading="test",
                aspect_ratio="16:9",
                visual_style="test",
                sound_design_notes="test",
            ),
            character_appearance_map={},
        )

        generator = SceneGenerator(api_key="test-key")
        # Should not raise any exception
        generator._validate_trailer_consistency(trailer)

    @patch("trailer_generator.scene_generator.OpenAI")
    def test_generate_trailer_without_narration(
        self, mock_openai_class, sample_movie, sample_trailer_data
    ):
        """Test trailer generation without narration."""
        # Remove narration from sample data
        data_without_narration = sample_trailer_data.copy()
        data_without_narration.pop("narration_script", None)

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(data_without_narration)

        mock_client.chat.completions.create.return_value = mock_response

        generator = SceneGenerator(api_key="test-key")
        trailer = generator.generate_trailer(movie=sample_movie, include_narration=False)

        assert trailer.narration_script is None

    @patch("trailer_generator.scene_generator.OpenAI")
    def test_generate_trailer_validates_output(self, mock_openai_class, sample_movie):
        """Test that generated trailer is validated before returning."""
        # Create invalid trailer data (uses reference_images but wrong duration)
        invalid_data = {
            "movie_title": "Test",
            "total_duration": 30,
            "character_designs": [
                {
                    "character_name": "Char_One",
                    "image_generation_prompt": "test",
                    "brief_identifier": "test",
                    "visual_style": "realistic",
                }
            ],
            "scenes": [
                {
                    "scene_number": 1,
                    "duration_seconds": 6,  # Invalid! Should be 8
                    "scene_type": "test",
                    "start_frame_prompt": "test",
                    "end_frame_prompt": "test",
                    "video_prompt": "test",
                    "reference_images": ["Char_One"],
                    "characters_present": [],
                }
            ],
            "technical_specs": {
                "color_grading": "test",
                "aspect_ratio": "16:9",
                "visual_style": "test",
                "sound_design_notes": "test",
            },
            "character_appearance_map": {},
        }

        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(invalid_data)

        mock_client.chat.completions.create.return_value = mock_response

        generator = SceneGenerator(api_key="test-key")

        with pytest.raises(SceneGeneratorError, match="exactly 8 seconds"):
            generator.generate_trailer(movie=sample_movie)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
