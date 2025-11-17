"""
Pydantic schemas for trailer generation.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# Input schemas (from mcp-screenplay movie generator)
class CastMember(BaseModel):
    """A cast member from the generated movie."""

    actor_name: str
    character_name: str
    physical_description: str
    personality_traits: List[str]
    acting_style: str
    role_description: str


class GeneratedMovie(BaseModel):
    """Movie data from mcp-screenplay movie generator."""

    title: str
    tagline: str
    genres: List[str]
    plot_summary: str
    director_name: str
    director_background: str
    writers: List[str]
    writer_backgrounds: str
    cast: List[CastMember]
    runtime: str
    rating: str
    release_year: int
    production_company: str
    production_company_background: str
    budget: str
    themes: List[str]
    visual_style: str
    target_audience: str
    inspiration_source: Optional[List[str]] = None
    unique_selling_point: Optional[str] = None
    similar_movies: Optional[List[str]] = None


# Request schemas
class TrailerRequest(BaseModel):
    """Request schema for trailer generation."""

    movie: GeneratedMovie = Field(
        ...,
        description="Complete movie data from movie generator"
    )

    target_duration: int = Field(
        default=35,
        ge=20,
        le=60,
        description="Target trailer duration in seconds (20-60)"
    )

    include_narration: bool = Field(
        default=True,
        description="Whether to include narration script"
    )

    model: Optional[str] = Field(
        None,
        description="OpenRouter model to use (overrides default)",
        examples=["anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-exp:free"]
    )


# Output schemas
class CharacterDesign(BaseModel):
    """Character design for reference image generation."""

    character_name: str = Field(
        ...,
        description="Character name (used as filename, e.g., 'Dr_Elara_Vance')"
    )

    image_generation_prompt: str = Field(
        ...,
        description="COMPLETE prompt for generating character reference image on pure white background. Must specify: visual style (hyper-realistic/animated/etc matching movie), full physical description (height, build, age, hair, eyes, features, clothing), pose (standing, facing camera, neutral expression), lighting (soft, even, no harsh shadows). Minimum 6-8 sentences."
    )

    brief_identifier: str = Field(
        ...,
        description="Short 3-5 word identifier for use in video prompts",
        examples=["slender woman, late 30s, dark hair", "imposing man, grey hair, military bearing"]
    )

    visual_style: str = Field(
        ...,
        description="Visual style matching movie aesthetic",
        examples=["hyper-realistic", "3D animated", "hand-drawn 2D animation", "claymation"]
    )


class TrailerScene(BaseModel):
    """A single scene in the trailer."""

    scene_number: int = Field(
        ...,
        description="Scene order number (1-indexed)"
    )

    duration_seconds: int = Field(
        ...,
        ge=4,
        le=10,
        description="Duration of this scene (typically 4-8 seconds, flexible)"
    )

    scene_type: str = Field(
        ...,
        description="Type of scene",
        examples=["establishing", "character_introduction", "action", "dialogue", "tension", "climax_tease"]
    )

    start_frame_prompt: str = Field(
        ...,
        description="SELF-CONTAINED prompt for start frame image generation. Must include ALL context: full physical descriptions of ANY characters (using brief_identifier), absolute positioning, complete lighting/color details, setting. NO references to other scenes. Minimum 4-5 sentences."
    )

    end_frame_prompt: str = Field(
        ...,
        description="SELF-CONTAINED prompt for end frame image generation. Must include ALL context independently. When characters present, identify using brief_identifier. NO references to other scenes. Minimum 4-5 sentences."
    )

    video_prompt: str = Field(
        ...,
        description="SELF-CONTAINED comprehensive prompt for VEO 3.1 video generation. CRITICAL: When characters present, identify each as 'CharacterName (brief_identifier)' e.g., 'Dr. Vance (slender woman, late 30s, dark hair)'. Must include: camera movement, motion direction, pacing, cinematography, specific actions/events, atmosphere, AND audio design naturally integrated. NO references to other scenes. Minimum 6-8 sentences."
    )

    reference_images: List[str] = Field(
        default_factory=list,
        description="List of character names (matching character_designs) to pass as VEO 3.1 reference images. Max 3. Empty list = no reference images. When not empty, duration_seconds MUST be 8."
    )

    characters_present: List[str] = Field(
        default_factory=list,
        description="List of all character names in this scene (metadata for tracking, not sent to models)"
    )

    continuity_note: Optional[str] = Field(
        None,
        description="Optional metadata note about this scene (not sent to models)"
    )


class TechnicalSpecs(BaseModel):
    """Technical specifications for the trailer."""

    color_grading: str = Field(
        ...,
        description="Overall color grading approach",
        examples=["Desaturated with teal shadows and amber highlights", "High contrast with deep blacks"]
    )

    aspect_ratio: str = Field(
        default="2.39:1",
        description="Aspect ratio for the trailer",
        examples=["2.39:1", "16:9", "1.85:1"]
    )

    visual_style: str = Field(
        ...,
        description="Overall visual aesthetic derived from movie's visual style"
    )

    sound_design_notes: str = Field(
        ...,
        description="General sound design approach for the trailer"
    )


class TrailerBreakdown(BaseModel):
    """Complete trailer scene breakdown."""

    movie_title: str = Field(
        ...,
        description="Title of the movie"
    )

    total_duration: int = Field(
        ...,
        description="Total trailer duration in seconds"
    )

    character_designs: List[CharacterDesign] = Field(
        ...,
        description="Character design prompts for generating reference images (generated BEFORE scenes)"
    )

    scenes: List[TrailerScene] = Field(
        ...,
        description="Ordered list of trailer scenes"
    )

    narration_script: Optional[str] = Field(
        None,
        description="Full narration script for ElevenLabs (if requested)"
    )

    continuity_guide: Optional[str] = Field(
        None,
        description="Guide for maintaining character consistency across scenes, including physical descriptions"
    )

    technical_specs: TechnicalSpecs = Field(
        ...,
        description="Technical specifications for video production"
    )

    character_appearance_map: Dict[str, List[int]] = Field(
        ...,
        description="Map of character names to scene numbers where they appear"
    )


class TrailerGenerationResponse(BaseModel):
    """Complete API response."""

    model_config = {"protected_namespaces": ()}

    success: bool = Field(
        ...,
        description="Whether generation was successful"
    )

    trailer: Optional[TrailerBreakdown] = Field(
        None,
        description="Generated trailer breakdown (null if failed)"
    )

    error: Optional[str] = Field(
        None,
        description="Error message if generation failed"
    )

    model_used: str = Field(
        ...,
        description="OpenRouter model that was used"
    )

    generation_time_seconds: Optional[float] = Field(
        None,
        description="Time taken to generate the trailer breakdown"
    )


class MovieAnalysis(BaseModel):
    """Analysis of the movie for trailer generation."""

    main_characters: List[Dict[str, str]] = Field(
        ...,
        description="Main characters with their names and physical descriptions"
    )

    key_themes: List[str] = Field(
        ...,
        description="Key themes to highlight in trailer"
    )

    visual_style_summary: str = Field(
        ...,
        description="Summary of visual style for consistent prompts"
    )

    tone: str = Field(
        ...,
        description="Overall tone of the movie",
        examples=["dark and gritty", "uplifting and hopeful", "tense and suspenseful"]
    )

    hook_elements: List[str] = Field(
        ...,
        description="Elements that would make compelling trailer hooks"
    )
