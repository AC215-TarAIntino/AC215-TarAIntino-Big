"""
Scene generator using OpenRouter LLM for trailer breakdown.
"""

import json
import logging
import time
from typing import Optional, Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)

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
        character_designs_context = analyzer.format_character_designs_for_llm()

        # Calculate recommended number of scenes
        # TESTING MODE: Only 2 scenes of 8 seconds each for quick/cheap testing
        # Note: Veo 3.1 REQUIRES 8 seconds when using reference images for character consistency
        num_scenes = "2"
        scene_duration = "8"  # 8 seconds per scene (required for reference images)

        # Original logic (commented out for now):
        # if target_duration <= 25:
        #     num_scenes = "4-5"
        # elif target_duration <= 35:
        #     num_scenes = "5-6"
        # elif target_duration <= 45:
        #     num_scenes = "6-8"
        # else:
        #     num_scenes = "8-10"

        narration_instruction = ""
        if include_narration:
            narration_instruction = """
  "narration_script": "A compelling narration script (2-4 sentences) that will be generated with ElevenLabs. This should be dramatic, hook the audience, and tease the story without spoiling it. Use short, punchy sentences.",
"""

        prompt = f"""You are an expert movie trailer editor and creative director. Your task is to create character designs and a detailed scene-by-scene breakdown for a {target_duration}-second movie trailer.

{movie_context}

{character_designs_context}

## TWO-PHASE GENERATION PROCESS

### PHASE 1: CHARACTER DESIGNS (Generate First!)

Before creating scenes, generate character designs for the top 4 main characters. These will be used to generate reference images.

**Character Design Requirements:**
- character_name: Format as "FirstName_LastName" (e.g., "Dr_Elara_Vance")
- image_generation_prompt: 6-8 sentence COMPLETE prompt for generating character reference image
  - MUST include: "standing on a pure white background"
  - MUST specify visual style matching movie (hyper-realistic, 3D animated, hand-drawn 2D animation, claymation, etc.)
  - Full physical description: height (e.g., "about 6 feet tall", NOT "6'0\""), build, age, hair (style/color), eyes, facial features, clothing
  - Pose: standing, facing camera, neutral expression
  - Lighting: soft, even, no harsh shadows
  - Camera: straight-on, full body or 3/4 body shot
- brief_identifier: 3-5 words for quick identification in video prompts (e.g., "slender woman, late 30s, dark hair")
- visual_style: Match movie aesthetic (let movie data guide you - hyper-realistic for gritty dramas, 3D animated for family films, etc.)

### PHASE 2: SCENE GENERATION

Create a trailer breakdown with EXACTLY {num_scenes} scenes. **CRITICAL FOR TESTING**: Each scene MUST be EXACTLY {scene_duration} seconds (for quick/cheap testing). No reference_images will be used.

## ⚠️ VEO 3.1 REFERENCE IMAGES SYSTEM

**CRITICAL**: VEO 3.1 supports up to 3 character reference images per scene. This maintains character consistency WITHOUT requiring continuous scenes!

**The New Approach:**
1. Pre-generate character reference images from character designs (orchestrator handles this)
2. Pass character reference images to VEO 3.1 via `referenceImages` parameter
3. Characters can appear in ANY scenes (not just continuous ones)

**VEO 3.1 Requirements with Reference Images:**
- Duration MUST be exactly 8 seconds when using reference images
- Maximum 3 reference images per scene (avoid 4+ character scenes)
- Aspect ratio: 16:9 (VEO 3.1 limitation with reference images)
- Parameter: `personGeneration: "allow_adult"` required

**When to Use Reference Images:**
- ANY scene with named characters should list them in `reference_images` array
- Use character_name format (e.g., "Dr_Elara_Vance")
- Empty list = no character focus (establishing shots, title cards, abstract sequences)

## SELF-CONTAINED PROMPTS (CRITICAL!)

**Each prompt will be sent to a separate AI model with ZERO context of other prompts.**

❌ BAD (references previous context):
- "The camera has risen higher..." (higher than what?)
- "She turns toward the chamber..." (who is she?)
- "Revealing more of the facility's scope..." (which facility?)
- "The lighting remains harsh..." (remains from what?)

✅ GOOD (completely self-contained):
- "Aerial view from 150 meters altitude of a brutalist research facility..."
- "Dr. Elara Vance, a slender woman in her late 30s with dark chestnut hair, turns toward..."
- "Wide shot of Project Cacophony research facility, a 300-meter tall grey structure..."
- "Harsh blue-white fluorescent lighting illuminates the sterile laboratory..."

**EVERY prompt must include:**
- Full character physical descriptions (every time they appear)
- Absolute measurements and positioning (not relative)
- Complete scene context and setting
- All lighting, color, and atmospheric details
- NO references to previous or next scenes

## TRAILER STRUCTURE GUIDANCE

Classic trailer flow (adapt to story):
1. **Hook/Establishing** (4-6s): Set the world
2. **Character Introduction** (6-8s): Protagonist with signature visual
3. **Conflict/Stakes** (6-8s): What's the problem?
4. **Action/Tension** (4-6s): Exciting moments
5. **Climax Tease** (4-6s): Peak moment
6. **Title Card** (2-4s): Optional

## PROMPT REQUIREMENTS

### start_frame_prompt (4-5 sentences, SELF-CONTAINED):
- **When characters present**: Identify each as "CharacterName (brief_identifier)" on first mention, e.g., "Dr. Vance (slender woman, late 30s, dark hair)"
- FULL character physical descriptions (height, build, age, hair, eyes, features, clothing)
- Specific lighting with absolute description ("harsh blue-white fluorescents at 6500K")
- Color palette and grading (teal shadows, amber highlights, etc.)
- Absolute positioning ("2 meters from camera", "center frame", "rule of thirds left")
- Camera angle with specifics ("eye level at 1.7m height", "low angle 30° up")
- Complete setting description

### end_frame_prompt (4-5 sentences, SELF-CONTAINED):
- **When characters present**: Identify each as "CharacterName (brief_identifier)"
- FULL character physical descriptions (complete, not relative to start)
- Final positioning, emotion, action (absolute, not "has turned" but "faces camera")
- Complete lighting and color (don't reference start, describe fully)
- Setting details (complete description)

### video_prompt (6-8 sentences, SELF-CONTAINED with AUDIO):
- **When characters present**: Identify each as "CharacterName (brief_identifier)" on first mention
- Camera movement (dolly in 2 meters over 6 seconds, crane up from ground to 20m, etc.)
- Subject movement (walks left to right 4 steps, turns 90° clockwise, etc.)
- Pacing and timing (slow 2-second pan, rapid 0.5s whip, etc.)
- Cinematography style (Steadicam, handheld, locked-off, etc.)
- Specific events with timing
- **AUDIO INTEGRATED NATURALLY**: Sound effects, ambient sounds, music style, dialogue
- Complete atmosphere description
- Visual style and color grading

**Example with audio integrated:**
"The camera executes a slow 6-second dolly forward toward Dr. Vance (slender woman, late 30s, dark hair), as she stands 3 meters away at a holographic interface in a sterile laboratory. Her long fingers trace complex patterns in the glowing blue holographic display while the lab equipment emits a steady low-frequency electronic hum at approximately 60Hz. Harsh blue-white fluorescent lights at 6500K illuminate the space from above, creating sharp shadows. Halfway through the dolly movement, the Chrysalids in the containment chamber behind her begin pulsing with synchronized bioluminescent light, producing harmonic crystalline tones that build from 440Hz to 880Hz. Dr. Vance's expression shifts from concentration to realization as she hears the harmonic pattern. She whispers with urgency: 'It's not a weapon... it's a language.' The crystalline tones crescendo and mix with her controlled breathing, creating tension."

## OUTPUT FORMAT

{{
  "movie_title": "{movie.title}",
  "total_duration": 16,  // {num_scenes} scenes × {scene_duration} seconds each
  "character_designs": [
    {{
      "character_name": "Dr_Elara_Vance",
      "image_generation_prompt": "COMPLETE 6-8 sentence prompt. Must specify visual style and include 'standing on a pure white background'. Full physical description, neutral pose, even lighting...",
      "brief_identifier": "slender woman, late 30s, dark hair",
      "visual_style": "hyper-realistic"
    }},
    {{
      "character_name": "General_Valerius_Kade",
      "image_generation_prompt": "...",
      "brief_identifier": "imposing man, grey hair, military bearing",
      "visual_style": "hyper-realistic"
    }}
  ],
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": {scene_duration},
      "scene_type": "character_introduction",
      "start_frame_prompt": "SELF-CONTAINED 4-5 sentence description. Characters identified as 'Dr. Vance (slender woman, late 30s, dark hair)'...",
      "end_frame_prompt": "SELF-CONTAINED 4-5 sentence description with COMPLETE context...",
      "video_prompt": "SELF-CONTAINED 6-8 sentence description. Characters identified as 'Dr. Vance (slender woman, late 30s, dark hair)'. Includes camera movement, action, AND audio naturally integrated...",
      "reference_images": ["Dr_Elara_Vance", "General_Valerius_Kade"],
      "characters_present": ["Dr. Elara Vance", "General Valerius Kade"],
      "continuity_note": "Optional metadata note"
    }},
    {{
      "scene_number": 2,
      "duration_seconds": {scene_duration},  // MUST be EXACTLY {scene_duration} seconds for testing
      "scene_type": "establishing",
      "start_frame_prompt": "SELF-CONTAINED description, no characters...",
      "end_frame_prompt": "SELF-CONTAINED complete description...",
      "video_prompt": "SELF-CONTAINED with audio integrated...",
      "reference_images": [],
      "characters_present": [],
      "continuity_note": "Wide establishing shot with no characters"
    }}
  ],{narration_instruction}
  "continuity_guide": "Brief guide for maintaining visual consistency across scenes...",
  "technical_specs": {{
    "color_grading": "...",
    "aspect_ratio": "16:9",
    "visual_style": "...",
    "sound_design_notes": "..."
  }},
  "character_appearance_map": {{
    "Dr. Elara Vance": [1],
    "General Valerius Kade": [1]
  }}
}}

## CRITICAL RULES - MUST FOLLOW

1. **Character designs first**: Generate character_designs array BEFORE scenes array
2. **Reference images**: Scenes with characters → list them in reference_images (max 3)
3. **8-second rule**: If reference_images is NOT empty, duration_seconds MUST be 8
4. **Character identification**: In ALL prompts, identify characters as "Name (brief_identifier)"
5. **Self-contained prompts**: ZERO references to other scenes, COMPLETE context every time
6. **Audio integration**: Naturally woven into video_prompt (no separate audio_notes field)
7. **Duration**: Each scene MUST be EXACTLY {scene_duration} seconds (testing mode - quick and cheap)
8. **Prompt length**: start/end 4-5 sentences, video 6-8 sentences
9. **Absolute descriptions**: No relative terms ("higher", "closer", "remains"), only absolute measurements
10. **Aspect ratio**: Use 16:9 for technical_specs (VEO 3.1 requirement with reference images)

Generate the trailer breakdown now. Return ONLY valid JSON."""

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

            # Parse JSON response with aggressive cleanup
            try:
                # Try to extract JSON if there's extra text
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    content = content[json_start:json_end]

                # Try strict parsing first
                try:
                    trailer_data = json.loads(content)
                except json.JSONDecodeError:
                    # If strict parsing fails, apply aggressive fixes for Claude/Llama output
                    import re

                    # Save original for debugging
                    original_content = content

                    # Fix 1: Replace all newlines with spaces (more aggressive)
                    content = re.sub(r'\s+', ' ', content)

                    # Fix 2: Remove trailing commas before closing brackets/braces
                    content = re.sub(r',(\s*[}\]])', r'\1', content)

                    # Fix 3: Fix missing commas between fields (common Claude/Llama issue)
                    content = re.sub(r'"\s+"', '", "', content)
                    content = re.sub(r'"\s*\]', '"]', content)
                    content = re.sub(r'"\s*\}', '"}', content)

                    # Fix missing commas after closing braces/brackets before quotes or braces
                    content = re.sub(r'}\s*"', '}, "', content)  # } " -> }, "
                    content = re.sub(r'}\s*{', '}, {', content)  # } { -> }, {
                    content = re.sub(r']\s*"', '], "', content)  # ] " -> ], "
                    content = re.sub(r']\s*{', '], {', content)  # ] { -> ], {
                    content = re.sub(r']\s*\[', '], [', content)  # ] [ -> ], [

                    # Fix 4: Fix common quote escaping issues
                    # Replace smart quotes with regular quotes
                    content = content.replace('"', '"').replace('"', '"')
                    content = content.replace(''', "'").replace(''', "'")

                    # Fix 5: Remove comments if any
                    content = re.sub(r'//.*?\n', '', content)
                    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

                    # Fix 6: Fix apostrophes in strings that might break JSON
                    # Replace escaped apostrophes with regular ones
                    content = content.replace("\\'", "'")

                    # Try parsing again
                    try:
                        trailer_data = json.loads(content)
                    except json.JSONDecodeError as e:
                        # Last resort: try to find and log the specific error location
                        error_pos = getattr(e, 'pos', None)
                        if error_pos:
                            context_start = max(0, error_pos - 100)
                            context_end = min(len(content), error_pos + 100)
                            error_context = content[context_start:context_end]
                            logger.error(f"JSON error at position {error_pos}: {error_context}")
                        raise
            except json.JSONDecodeError as e:
                raise SceneGeneratorError(
                    f"Failed to parse LLM response as JSON: {e}\nResponse: {content[:500]}..."
                )

            # Validate and create TrailerBreakdown object
            try:
                trailer_breakdown = TrailerBreakdown(**trailer_data)

                # Validate consistency rules
                self._validate_trailer_consistency(trailer_breakdown)

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

    def _validate_trailer_consistency(self, trailer: TrailerBreakdown) -> None:
        """
        Validate reference images constraints.

        Args:
            trailer: TrailerBreakdown to validate

        Raises:
            SceneGeneratorError: If validation fails
        """
        scenes = trailer.scenes
        character_designs = trailer.character_designs

        # Build set of available character names for validation
        available_characters = {design.character_name for design in character_designs}

        # Validate each scene
        for scene in scenes:
            # Rule 1: If reference_images is not empty, duration must be 8 seconds
            if scene.reference_images:
                if scene.duration_seconds != 8:
                    raise SceneGeneratorError(
                        f"Scene {scene.scene_number}: Uses reference_images but duration is "
                        f"{scene.duration_seconds}s. VEO 3.1 requires exactly 8 seconds when using reference images."
                    )

            # Rule 2: Maximum 3 reference images per scene
            if len(scene.reference_images) > 3:
                raise SceneGeneratorError(
                    f"Scene {scene.scene_number}: Has {len(scene.reference_images)} reference images. "
                    f"VEO 3.1 supports maximum 3 reference images per scene."
                )

            # Rule 3: All reference_images must exist in character_designs
            for ref_char in scene.reference_images:
                if ref_char not in available_characters:
                    raise SceneGeneratorError(
                        f"Scene {scene.scene_number}: References character '{ref_char}' but this character "
                        f"is not in character_designs. Available characters: {sorted(available_characters)}"
                    )
