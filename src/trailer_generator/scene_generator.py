"""
Scene generator using OpenRouter LLM for trailer breakdown.
"""

import json
import time
from typing import Optional, Dict, List
from openai import OpenAI

from .config import settings
from .schemas import (
    GeneratedMovie,
    TrailerBreakdown,
    TrailerScene,
    TechnicalSpecs,
)
from .scene_analyzer import MovieAnalyzer


class SceneGeneratorError(Exception):
    """Base exception for scene generator errors."""
    pass


class SceneGenerator:
    """Generates trailer scene breakdowns using LLM."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize the scene generator.

        Args:
            api_key: OpenRouter API key
            model: Model to use
            base_url: Base URL for OpenRouter
        """
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or settings.openrouter_model
        self.base_url = base_url or settings.openrouter_base_url

        # Initialize OpenAI client with OpenRouter
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _create_generation_prompt(
        self,
        movie: GeneratedMovie,
        target_duration: int,
        include_narration: bool
    ) -> str:
        """
        Create the detailed prompt for trailer scene generation.

        Args:
            movie: GeneratedMovie object
            target_duration: Target trailer duration in seconds
            include_narration: Whether to include narration

        Returns:
            Complete prompt for the LLM
        """
        # Analyze the movie
        analyzer = MovieAnalyzer(movie)
        movie_context = analyzer.format_for_llm_context()
        character_guide = analyzer.get_character_consistency_guide()

        # Calculate recommended number of scenes
        if target_duration <= 25:
            num_scenes = "4-5"
        elif target_duration <= 35:
            num_scenes = "5-6"
        elif target_duration <= 45:
            num_scenes = "6-8"
        else:
            num_scenes = "8-10"

        narration_instruction = ""
        if include_narration:
            narration_instruction = """
  "narration_script": "A compelling narration script (2-4 sentences) that will be generated with ElevenLabs. This should be dramatic, hook the audience, and tease the story without spoiling it. Use short, punchy sentences.",
"""

        prompt = f"""You are an expert movie trailer editor and creative director. Your task is to create a detailed scene-by-scene breakdown for a {target_duration}-second movie trailer.

{movie_context}

{character_guide}

## YOUR TASK

Create a trailer breakdown with {num_scenes} scenes. Each scene should be 4, 6, or 8 seconds long (total ~{target_duration} seconds).

## CRITICAL RULES FOR CHARACTER CONSISTENCY

⚠️ **CHARACTER CONTINUITY IS ESSENTIAL**:
1. When a character appears in multiple parts of the trailer, they MUST appear in ONE CONTINUOUS SCENE
2. Example: If "Dr. Vance" appears at the beginning and middle, create ONE 8-second scene showing both moments
3. This is because VEO 3.1 maintains consistency by using end_frame → start_frame continuity
4. The LAST FRAME of scene N becomes the FIRST FRAME of scene N+1
5. Only separate character appearances into different scenes if there's a dramatic location/time change

## TRAILER STRUCTURE GUIDANCE

A great trailer typically follows this flow:
1. **Hook/Establishing** (4-6s): Set the world, create intrigue
2. **Character Introduction** (6-8s): Introduce protagonist(s) with their visual signature
3. **Conflict/Stakes** (6-8s): What's the problem? What's at stake?
4. **Action/Tension** (4-6s): Show exciting moments, build energy
5. **Climax Tease** (4-6s): Peak moment, ultimate hook
6. **Title Card** (2-4s): Movie title reveal (can be scene or post-production)

## PROMPT REQUIREMENTS

For EACH scene, you must provide:

### start_frame_prompt (4-5 sentences minimum):
- Exact character physical descriptions from the consistency guide
- Specific lighting (e.g., "rim lighting from behind", "harsh overhead fluorescents")
- Color palette (reference the movie's visual style)
- Composition (rule of thirds, center frame, etc.)
- Camera angle (low angle, dutch tilt, eye level, etc.)
- Setting details

Example:
"Dr. Elara Vance, a slender woman in her late 30s with long dark chestnut hair in a messy bun, stands in profile against a massive transparent observation window. She has hazel eyes and delicate features, wearing a grey Dominion lab coat. The lighting is cold and clinical, with harsh blue-white fluorescents creating a desaturated, sterile atmosphere. Behind her through the window, bioluminescent alien creatures pulse with amber and teal light. Shot with shallow depth of field at eye level, her face is sharply focused while the background softly glows. Color grading: teal shadows, amber highlights, desaturated skin tones."

### end_frame_prompt (4-5 sentences minimum):
- Show PROGRESSION from the start frame
- Describe the final position/emotion/action
- Maintain character consistency
- Same lighting and color palette guidelines
- This becomes the NEXT scene's start frame

### video_prompt (5-7 sentences minimum):
- **EXPLICIT MOTION DESCRIPTION** (this is crucial for VEO 3.1)
- Camera movement (dolly in, crane up, handheld tracking, static, etc.)
- Subject movement (turns toward camera, runs left to right, etc.)
- Pacing (slow and deliberate, rapid and frenetic)
- Cinematography style (Steadicam flow, handheld realism, locked-off elegance)
- Specific events that occur
- Atmosphere and mood evolution
- Reference the movie's visual style

Example:
"The camera slowly dollies in toward Dr. Vance (steady, deliberate movement taking 6 seconds) as she remains in profile. Halfway through, she slowly turns her head toward the camera, her hazel eyes widening with a mix of fear and determination. The bioluminescent creatures behind her pulse faster, their light intensifying from a soft glow to a bright amber strobe, casting shifting shadows across her face. The camera movement is smooth and cinematic, evoking the measured pacing of Denis Villeneuve. Sound design: deep ambient hum building to a resonant bass pulse. Maintain the cold, desaturated color grading throughout with teal shadows and amber highlights from the alien light source."

### audio_notes:
Describe the sound design: ambient sounds, music style (orchestral swell, electronic pulse, etc.), dialogue snippets if any, sound effects

## OUTPUT FORMAT

Respond ONLY with valid JSON in this EXACT structure:

{{
  "movie_title": "{movie.title}",
  "total_duration": {target_duration},
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 6,
      "scene_type": "establishing",
      "start_frame_prompt": "Detailed 4-5 sentence prompt with character descriptions, lighting, composition, color...",
      "end_frame_prompt": "Detailed 4-5 sentence prompt showing progression...",
      "video_prompt": "Detailed 5-7 sentence prompt with explicit camera movement, subject motion, pacing, cinematography style...",
      "characters_present": ["Character Name 1", "Character Name 2"],
      "audio_notes": "Sound design description...",
      "continuity_note": "Optional note about continuity"
    }}
  ],{narration_instruction}
  "continuity_guide": "Summary of character physical descriptions for consistency...",
  "technical_specs": {{
    "color_grading": "Description based on movie's visual style...",
    "aspect_ratio": "2.39:1",
    "visual_style": "Summary...",
    "sound_design_notes": "Overall sound design approach..."
  }},
  "character_appearance_map": {{
    "Character Name 1": [1, 3],
    "Character Name 2": [2, 4]
  }}
}}

## CRITICAL FORMATTING REQUIREMENTS

⚠️ STRICT RULES - DO NOT DEVIATE:
1. **duration_seconds**: MUST be an integer between 4 and 8 (typically 4, 5, 6, 7, or 8). NO scenes shorter than 4 seconds or longer than 8 seconds.
2. **continuity_guide**: MUST be a single STRING (not a dict, not an object). Write it as a multi-line text description.
3. **Total duration**: All scene durations added together should equal approximately {target_duration} seconds
4. **Character consistency**: Characters appearing multiple times = ONE continuous scene
5. **Frame continuity**: End frame of scene N = Start frame of scene N+1
6. **Prompt detail**: ALL prompts must be HIGHLY DETAILED (minimum sentence counts specified)
7. **Motion description**: Video prompts MUST explicitly describe camera and subject motion
8. **Visual consistency**: Reference the movie's visual style and color grading in every prompt

**Example of correct continuity_guide format:**
"continuity_guide": "Dr. Elara Vance: Slender woman, late 30s, 5'7\\", dark chestnut hair in messy bun, hazel eyes, delicate features... General Kade: Imposing man, early 50s, 6'2\\", athletic build, steel grey hair..."

Generate the trailer breakdown now. Return ONLY valid JSON matching the exact structure shown above, no additional text."""

        return prompt

    def generate_trailer(
        self,
        movie: GeneratedMovie,
        target_duration: int = 35,
        include_narration: bool = True,
        model_override: Optional[str] = None
    ) -> TrailerBreakdown:
        """
        Generate a trailer scene breakdown.

        Args:
            movie: GeneratedMovie object
            target_duration: Target trailer duration in seconds
            include_narration: Whether to include narration script
            model_override: Optional model to use instead of default

        Returns:
            TrailerBreakdown object

        Raises:
            SceneGeneratorError: If generation fails
        """
        model_to_use = model_override or self.model
        prompt = self._create_generation_prompt(movie, target_duration, include_narration)

        try:
            # Create chat completion
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert movie trailer editor and creative director. You generate detailed, structured trailer breakdowns in JSON format. You always follow instructions precisely and create highly detailed prompts for AI video generation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )

            generation_time = time.time() - start_time

            # Extract the generated content
            content = response.choices[0].message.content

            if not content:
                raise SceneGeneratorError("Empty response from LLM")

            # Parse JSON response
            try:
                # Try to extract JSON if there's extra text
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    content = content[json_start:json_end]

                trailer_data = json.loads(content)
            except json.JSONDecodeError as e:
                raise SceneGeneratorError(
                    f"Failed to parse LLM response as JSON: {e}\nResponse: {content[:500]}..."
                )

            # Validate and create TrailerBreakdown object
            try:
                trailer_breakdown = TrailerBreakdown(**trailer_data)
                return trailer_breakdown
            except Exception as e:
                raise SceneGeneratorError(
                    f"Failed to validate trailer breakdown data: {e}\nData keys: {trailer_data.keys()}"
                )

        except Exception as e:
            if isinstance(e, SceneGeneratorError):
                raise
            raise SceneGeneratorError(f"Failed to generate trailer: {str(e)}")

    def _build_character_appearance_map(
        self,
        scenes: List[TrailerScene]
    ) -> Dict[str, List[int]]:
        """
        Build a map of character names to scene numbers.

        Args:
            scenes: List of TrailerScene objects

        Returns:
            Dictionary mapping character names to scene numbers
        """
        character_map: Dict[str, List[int]] = {}

        for scene in scenes:
            for character in scene.characters_present:
                if character not in character_map:
                    character_map[character] = []
                character_map[character].append(scene.scene_number)

        return character_map
