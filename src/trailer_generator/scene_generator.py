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

Create a trailer breakdown with {num_scenes} scenes. Each scene should be 4-8 seconds long (total ~{target_duration} seconds).

## ⚠️ ABSOLUTE RULE: CHARACTER CONSISTENCY ACROSS SCENES

**CRITICAL**: Video generation models (VEO 3.1) have NO MEMORY between API calls. Each prompt is independent.

**THE RULE**: If a character appears in Scene N and Scene M (where M > N+1), ALL scenes between them MUST form a continuous chain using `uses_previous_end_frame: true`.

**Why?** VEO 3.1 maintains character consistency only through frame continuity (end_frame → start_frame). Without this, the character will look different across scenes.

**Examples:**

✅ CORRECT - Character A appears in 3 continuous scenes:
```
Scene 1: Character A (uses_previous_end_frame: false, start_frame_prompt: "...")
Scene 2: Character A + B (uses_previous_end_frame: true, start_frame_prompt: null)
Scene 3: Character A alone (uses_previous_end_frame: true, start_frame_prompt: null)
Scene 4: Character B only (uses_previous_end_frame: false, start_frame_prompt: "...")
```

❌ WRONG - Character A in non-continuous scenes:
```
Scene 1: Character A (uses_previous_end_frame: false)
Scene 2: Character B (uses_previous_end_frame: false) ← CUT, breaks continuity
Scene 3: Character A again (uses_previous_end_frame: false) ← WRONG! Can't maintain consistency!
```

**Decision Making**: Use story flow to decide on cuts vs. continuity. BUT if a character must appear twice, make those appearances continuous.

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
- FULL character physical descriptions (height, build, age, hair, eyes, features, clothing)
- Specific lighting with absolute description ("harsh blue-white fluorescents at 6500K")
- Color palette and grading (teal shadows, amber highlights, etc.)
- Absolute positioning ("2 meters from camera", "center frame", "rule of thirds left")
- Camera angle with specifics ("eye level at 1.7m height", "low angle 30° up")
- Complete setting description

**Set to NULL when `uses_previous_end_frame: true`**

### end_frame_prompt (4-5 sentences, SELF-CONTAINED):
- FULL character physical descriptions (complete, not relative to start)
- Final positioning, emotion, action (absolute, not "has turned" but "faces camera")
- Complete lighting and color (don't reference start, describe fully)
- Setting details (complete description)
- This will become next scene's START FRAME if continuous

### video_prompt (6-8 sentences, SELF-CONTAINED with AUDIO):
- Camera movement (dolly in 2 meters over 6 seconds, crane up from ground to 20m, etc.)
- Subject movement (walks left to right 4 steps, turns 90° clockwise, etc.)
- Pacing and timing (slow 2-second pan, rapid 0.5s whip, etc.)
- Cinematography style (Steadicam, handheld, locked-off, etc.)
- Specific events with timing
- **AUDIO INTEGRATED NATURALLY**: Sound effects, ambient sounds, music style, dialogue
- Complete atmosphere description
- Visual style and color grading

**Example with audio integrated:**
"The camera executes a slow 6-second dolly forward toward Dr. Elara Vance, a slender woman in her late 30s with long dark chestnut hair in a messy bun and hazel eyes, as she stands 3 meters away at a holographic interface in a sterile laboratory. Her long fingers trace complex patterns in the glowing blue holographic display while the lab equipment emits a steady low-frequency electronic hum at approximately 60Hz. Harsh blue-white fluorescent lights at 6500K illuminate the space from above, creating sharp shadows. Halfway through the dolly movement, the Chrysalids in the containment chamber behind her begin pulsing with synchronized bioluminescent light, producing harmonic crystalline tones that build from 440Hz to 880Hz. Dr. Vance's expression shifts from concentration to realization as she hears the harmonic pattern. She whispers with urgency: 'It's not a weapon... it's a language.' The crystalline tones crescendo and mix with her controlled breathing, creating tension."

## OUTPUT FORMAT

{{
  "movie_title": "{movie.title}",
  "total_duration": {target_duration},
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 6,
      "scene_type": "establishing",
      "uses_previous_end_frame": false,
      "start_frame_prompt": "SELF-CONTAINED 4-5 sentence description with COMPLETE context...",
      "end_frame_prompt": "SELF-CONTAINED 4-5 sentence description with COMPLETE context...",
      "video_prompt": "SELF-CONTAINED 6-8 sentence description with camera movement, action, AND audio naturally integrated...",
      "characters_present": ["Character Name"],
      "continuity_note": "Optional metadata note"
    }},
    {{
      "scene_number": 2,
      "duration_seconds": 7,
      "scene_type": "character_introduction",
      "uses_previous_end_frame": true,
      "start_frame_prompt": null,
      "end_frame_prompt": "SELF-CONTAINED complete description...",
      "video_prompt": "SELF-CONTAINED with audio integrated...",
      "characters_present": ["Character Name"],
      "continuity_note": "Continuous from scene 1"
    }}
  ],{narration_instruction}
  "continuity_guide": "SINGLE STRING with character descriptions...",
  "technical_specs": {{
    "color_grading": "...",
    "aspect_ratio": "2.39:1",
    "visual_style": "...",
    "sound_design_notes": "..."
  }},
  "character_appearance_map": {{
    "Character Name": [1, 2]
  }}
}}

## CRITICAL RULES - MUST FOLLOW

1. **Character consistency**: Same character in multiple scenes → continuous chain with `uses_previous_end_frame: true`
2. **Self-contained prompts**: ZERO references to other scenes, COMPLETE context every time
3. **Audio integration**: Naturally woven into video_prompt (no separate audio_notes field)
4. **Continuity flag**: `uses_previous_end_frame: true` means `start_frame_prompt: null`
5. **Duration**: 4-8 seconds per scene, total ~{target_duration} seconds
6. **Prompt length**: start/end 4-5 sentences, video 6-8 sentences
7. **Absolute descriptions**: No relative terms ("higher", "closer", "remains"), only absolute measurements

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
        Validate character consistency and continuity rules.

        Args:
            trailer: TrailerBreakdown to validate

        Raises:
            SceneGeneratorError: If validation fails
        """
        scenes = trailer.scenes

        # Validate each scene
        for i, scene in enumerate(scenes):
            # Rule 1: uses_previous_end_frame => start_frame_prompt must be null
            if scene.uses_previous_end_frame:
                if scene.start_frame_prompt is not None:
                    raise SceneGeneratorError(
                        f"Scene {scene.scene_number}: uses_previous_end_frame=true but "
                        f"start_frame_prompt is not null. It should be null to reuse previous end_frame."
                    )

                # Rule 2: First scene cannot use previous end frame
                if i == 0:
                    raise SceneGeneratorError(
                        f"Scene {scene.scene_number}: First scene cannot have uses_previous_end_frame=true"
                    )

            # Rule 3: If not using previous end frame, must have start_frame_prompt
            else:
                if scene.start_frame_prompt is None:
                    raise SceneGeneratorError(
                        f"Scene {scene.scene_number}: uses_previous_end_frame=false but "
                        f"start_frame_prompt is null. It must have a complete prompt."
                    )

        # Rule 4: Character consistency - characters appearing in multiple non-adjacent scenes
        # must be connected by continuous scenes
        character_scenes = {}
        for scene in scenes:
            for char in scene.characters_present:
                if char not in character_scenes:
                    character_scenes[char] = []
                character_scenes[char].append(scene.scene_number)

        for char, scene_nums in character_scenes.items():
            if len(scene_nums) > 1:
                # Check if scenes form a continuous chain
                # For each pair of appearances, check if connected by uses_previous_end_frame chain
                for i in range(len(scene_nums) - 1):
                    current_scene_num = scene_nums[i]
                    next_scene_num = scene_nums[i + 1]

                    # If not adjacent, check if all scenes between them form continuous chain
                    if next_scene_num > current_scene_num + 1:
                        # Check intermediate scenes
                        for intermediate_scene_num in range(current_scene_num + 1, next_scene_num):
                            # Find scene object
                            intermediate_scene = next(s for s in scenes if s.scene_number == intermediate_scene_num)

                            # Must use previous end frame to maintain continuity
                            if not intermediate_scene.uses_previous_end_frame:
                                raise SceneGeneratorError(
                                    f"Character '{char}' appears in scenes {current_scene_num} and {next_scene_num}, "
                                    f"but scene {intermediate_scene_num} breaks the continuity chain with "
                                    f"uses_previous_end_frame=false. For character consistency, all scenes between "
                                    f"character appearances must be continuous (uses_previous_end_frame=true)."
                                )

                    # If adjacent, next scene must use previous end frame
                    elif next_scene_num == current_scene_num + 1:
                        next_scene = next(s for s in scenes if s.scene_number == next_scene_num)
                        if not next_scene.uses_previous_end_frame:
                            raise SceneGeneratorError(
                                f"Character '{char}' appears in consecutive scenes {current_scene_num} and {next_scene_num}, "
                                f"but scene {next_scene_num} has uses_previous_end_frame=false. For character consistency, "
                                f"the next scene must use the previous end frame (uses_previous_end_frame=true)."
                            )
