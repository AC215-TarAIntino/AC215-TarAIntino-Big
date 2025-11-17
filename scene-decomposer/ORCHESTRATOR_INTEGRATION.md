# Orchestrator Integration Guide

Complete guide for integrating `mcp-trailer-generator` with your video orchestration service using VEO 3.1's reference images system.

## Table of Contents

1. [Overview](#overview)
2. [Understanding the Output](#understanding-the-output)
3. [Complete Workflow](#complete-workflow)
4. [VEO 3.1 API Requirements](#veo-31-api-requirements)
5. [Implementation Examples](#implementation-examples)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## Overview

The trailer generator outputs a **two-phase structure**:

1. **Phase 1: Character Designs** - Prompts to generate character reference images
2. **Phase 2: Scenes** - Scene-by-scene prompts that reference those characters

Your orchestrator must:
1. Generate character reference images from Phase 1
2. Use those images with VEO 3.1's `referenceImages` parameter in Phase 2
3. Stitch the final videos together

---

## Understanding the Output

### JSON Structure

```json
{
  "movie_title": "Example Movie",
  "total_duration": 35,

  "character_designs": [
    {
      "character_name": "Dr_Elara_Vance",
      "image_generation_prompt": "A slender woman in her late 30s with long dark chestnut hair tied in a messy bun and warm hazel eyes, standing on a pure white background. She has an intelligent, focused expression. Wearing a fitted grey lab coat over a simple black shirt. Hyper-realistic style with precise anatomical detail. Standing facing camera in neutral pose, 3/4 body shot at 1.7m camera height. Soft, even lighting with no harsh shadows, 5500K color temperature.",
      "brief_identifier": "slender woman, late 30s, dark hair",
      "visual_style": "hyper-realistic"
    }
  ],

  "scenes": [
    {
      "scene_number": 1,
      "duration_seconds": 8,
      "scene_type": "character_introduction",
      "start_frame_prompt": "Dr. Vance (slender woman, late 30s, dark hair) stands at a holographic interface in a sterile laboratory. Harsh blue-white fluorescent lights at 6500K illuminate the space from above, creating sharp shadows. She is positioned 2 meters from camera at eye level, centered in frame. The laboratory features glass containment chambers and metallic surfaces with a cold, clinical atmosphere.",
      "end_frame_prompt": "Dr. Vance (slender woman, late 30s, dark hair) stands transfixed before the containment chamber, her hazel eyes wide with wonder. Shimmering auroras of light dance around her. Her long fingers trace patterns in the air. The chamber is bathed in shifting colors from violet to emerald, casting dynamic shadows across her face.",
      "video_prompt": "The camera executes a slow 6-second dolly forward toward Dr. Vance (slender woman, late 30s, dark hair) as she stands 3 meters away at a holographic interface. Her fingers trace complex patterns in the glowing blue display while lab equipment emits a steady 60Hz electronic hum. Halfway through, entities in the chamber begin pulsing with light, producing harmonic crystalline tones from 440Hz to 880Hz. Dr. Vance's expression shifts from concentration to realization. She whispers: 'It's not a weapon... it's a language.' The tones crescendo, mixing with her breathing.",
      "reference_images": ["Dr_Elara_Vance"],
      "characters_present": ["Dr. Elara Vance"],
      "continuity_note": "Introduces protagonist discovering the truth"
    },
    {
      "scene_number": 2,
      "duration_seconds": 6,
      "scene_type": "establishing",
      "start_frame_prompt": "Wide aerial view from 200 meters altitude of a massive brutalist research facility rising 300 meters into a purple-tinged alien sky. The grey angular structure features glowing blue energy conduits. Three military hoverships patrol the perimeter. Below, bioluminescent jungle canopy teems with floating golden spores.",
      "end_frame_prompt": "The aerial view has descended to 100 meters, revealing the facility's main courtyard where dozens of personnel in white hazmat suits move between buildings. Security drones hover overhead. The purple sky creates an otherworldly atmosphere.",
      "video_prompt": "Sweeping drone shot executing a 6-second descent from 200m to 100m altitude, combined with a slow 180-degree rotation around the facility. Deep bass rumbles at 40Hz mix with hovership engine whines. Wind sounds at varying pitches create tension. The camera reveals the scale of the operation through layers of mist. Mechanical security system sounds echo. No dialogue.",
      "reference_images": [],
      "characters_present": [],
      "continuity_note": "Establishes scale and setting"
    }
  ],

  "narration_script": "In a world where sound shapes reality, they thought they found a weapon. Instead, they discovered a language older than time itself.",

  "technical_specs": {
    "color_grading": "Strong contrast between cold facility scenes (desaturated blues/greys) and alien environment (rich purples with bioluminescent accents)",
    "aspect_ratio": "16:9",
    "visual_style": "Combination of rigid, symmetrical compositions for facility and fluid, organic movement for exterior",
    "sound_design_notes": "Complex layering of frequencies with natural/mechanical sounds. Harmonic progression builds throughout."
  },

  "character_appearance_map": {
    "Dr. Elara Vance": [1, 3, 5]
  }
}
```

### Key Fields Explained

#### character_designs Array

- **character_name**: Use as filename (e.g., `Dr_Elara_Vance.png`)
- **image_generation_prompt**: Complete prompt for DALL-E/Flux
  - ALWAYS includes "standing on a pure white background"
  - Specifies visual style (hyper-realistic, 3D animated, etc.)
  - 6-8 sentences with full physical description
- **brief_identifier**: Short description used in scene prompts
- **visual_style**: Matches movie aesthetic

#### scenes Array

- **reference_images**: List of character_name values to use as references
  - Empty list `[]` = no characters in scene
  - 1-3 names = use those character reference images with VEO
- **duration_seconds**:
  - 8 seconds if `reference_images` is not empty (VEO requirement)
  - 4-8 seconds if `reference_images` is empty
- **Prompts mention characters as**: "Name (brief_identifier)"
  - Example: "Dr. Vance (slender woman, late 30s, dark hair)"

---

## Complete Workflow

### Step-by-Step Process

```
1. Call mcp-trailer-generator API
   ↓
2. Receive JSON with character_designs + scenes
   ↓
3. PHASE 1: Generate Character Reference Images
   - For each character_design:
     - Generate image using image_generation_prompt
     - Save as character_name.png
   ↓
4. PHASE 2: Generate Scene Videos
   - For each scene:
     - Generate start_frame image
     - Generate end_frame image
     - Load character references (if any)
     - Call VEO 3.1 with references
   ↓
5. Stitch videos together
   ↓
6. Add narration (if present)
   ↓
7. Export final trailer
```

---

## VEO 3.1 API Requirements

### With Reference Images (Character Scenes)

When `scene.reference_images` is **NOT empty**:

```python
{
  "prompt": scene["video_prompt"],
  "image": start_frame_image,
  "lastFrame": end_frame_image,
  "duration": 8,  # MUST be 8 seconds
  "aspectRatio": "16:9",  # MUST be 16:9
  "referenceImages": [
    character_ref_image_1,  # Base64 or URL
    character_ref_image_2,  # Up to 3 max
  ],
  "personGeneration": "allow_adult"  # REQUIRED with referenceImages
}
```

**Critical Requirements:**
- ✅ `duration` MUST be exactly 8 seconds
- ✅ `aspectRatio` MUST be "16:9"
- ✅ `referenceImages` max 3 images
- ✅ `personGeneration: "allow_adult"` REQUIRED
- ✅ Each reference image must be the character on white background

### Without Reference Images (Non-Character Scenes)

When `scene.reference_images` is **empty**:

```python
{
  "prompt": scene["video_prompt"],
  "image": start_frame_image,
  "lastFrame": end_frame_image,
  "duration": scene["duration_seconds"],  # 4-8 seconds
  "aspectRatio": "16:9"  # or other ratios
}
```

**Flexible Requirements:**
- ✅ Duration can be 4-8 seconds
- ✅ Aspect ratio flexible (but 16:9 recommended for consistency)
- ✅ No personGeneration parameter needed

---

## Implementation Examples

### Complete Python Implementation

```python
import requests
import base64
from typing import Dict, List, Optional
from pathlib import Path


class TrailerOrchestrator:
    """Orchestrates trailer generation using mcp-trailer-generator."""

    def __init__(
        self,
        generator_url: str = "http://localhost:8001",
        image_api_key: str = None,  # DALL-E or Flux API key
        veo_api_key: str = None,
        output_dir: str = "trailer_output"
    ):
        self.generator_url = generator_url
        self.image_api_key = image_api_key
        self.veo_api_key = veo_api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_trailer(self, movie_data: dict) -> Path:
        """
        Generate complete trailer from movie data.

        Args:
            movie_data: Movie JSON from mcp-screenplay

        Returns:
            Path to final trailer video
        """
        # Step 1: Get trailer breakdown
        print("🎬 Generating trailer breakdown...")
        breakdown = self._get_trailer_breakdown(movie_data)

        # Step 2: Generate character reference images
        print(f"\n👥 Generating {len(breakdown['character_designs'])} character references...")
        character_refs = self._generate_character_references(
            breakdown['character_designs']
        )

        # Step 3: Generate scene videos
        print(f"\n🎥 Generating {len(breakdown['scenes'])} scene videos...")
        scene_videos = self._generate_scene_videos(
            breakdown['scenes'],
            character_refs
        )

        # Step 4: Stitch videos
        print("\n✂️ Stitching scenes together...")
        final_video = self._stitch_videos(scene_videos)

        # Step 5: Add narration (if present)
        if breakdown.get('narration_script'):
            print("\n🎙️ Adding narration...")
            final_video = self._add_narration(
                final_video,
                breakdown['narration_script']
            )

        print(f"\n✅ Trailer complete: {final_video}")
        return final_video

    def _get_trailer_breakdown(self, movie_data: dict) -> dict:
        """Call mcp-trailer-generator API."""
        response = requests.post(
            f"{self.generator_url}/generate-trailer",
            json={
                "movie": movie_data,
                "target_duration": 35,
                "include_narration": True
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        if not result['success']:
            raise Exception(f"Generation failed: {result.get('error')}")

        return result['trailer']

    def _generate_character_references(
        self,
        character_designs: List[dict]
    ) -> Dict[str, str]:
        """
        Generate character reference images from designs.

        Args:
            character_designs: List of CharacterDesign objects

        Returns:
            Dict mapping character_name to image path
        """
        character_refs = {}

        for i, design in enumerate(character_designs, 1):
            char_name = design['character_name']
            prompt = design['image_generation_prompt']

            print(f"  [{i}/{len(character_designs)}] Generating {char_name}...")

            # Generate image using DALL-E or Flux
            image_data = self._generate_image(prompt)

            # Save image
            image_path = self.output_dir / f"refs/{char_name}.png"
            image_path.parent.mkdir(exist_ok=True)
            image_path.write_bytes(image_data)

            character_refs[char_name] = str(image_path)
            print(f"    ✓ Saved to {image_path}")

        return character_refs

    def _generate_scene_videos(
        self,
        scenes: List[dict],
        character_refs: Dict[str, str]
    ) -> List[Path]:
        """
        Generate videos for all scenes.

        Args:
            scenes: List of scene objects
            character_refs: Dict of character_name -> image_path

        Returns:
            List of video file paths
        """
        scene_videos = []

        for scene in scenes:
            scene_num = scene['scene_number']
            print(f"\n  Scene {scene_num}: {scene['scene_type']} ({scene['duration_seconds']}s)")

            # Generate start and end frames
            print(f"    Generating start frame...")
            start_img = self._generate_image(scene['start_frame_prompt'])

            print(f"    Generating end frame...")
            end_img = self._generate_image(scene['end_frame_prompt'])

            # Prepare reference images for this scene
            scene_ref_images = []
            if scene['reference_images']:
                print(f"    Loading {len(scene['reference_images'])} character reference(s)...")
                for char_name in scene['reference_images']:
                    ref_path = character_refs[char_name]
                    scene_ref_images.append(Path(ref_path).read_bytes())
                    print(f"      ✓ {char_name}")

            # Call VEO 3.1
            print(f"    Generating video with VEO 3.1...")
            video_data = self._generate_video_veo(
                prompt=scene['video_prompt'],
                start_frame=start_img,
                end_frame=end_img,
                duration=scene['duration_seconds'],
                reference_images=scene_ref_images
            )

            # Save video
            video_path = self.output_dir / f"scenes/scene_{scene_num:02d}.mp4"
            video_path.parent.mkdir(exist_ok=True)
            video_path.write_bytes(video_data)

            scene_videos.append(video_path)
            print(f"    ✓ Saved to {video_path}")

        return scene_videos

    def _generate_image(self, prompt: str) -> bytes:
        """
        Generate image using DALL-E or Flux.

        Args:
            prompt: Image generation prompt

        Returns:
            Image data as bytes
        """
        # Example using OpenAI DALL-E 3
        import openai

        client = openai.OpenAI(api_key=self.image_api_key)

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )

        # Download image
        import urllib.request
        image_url = response.data[0].url
        with urllib.request.urlopen(image_url) as response:
            return response.read()

    def _generate_video_veo(
        self,
        prompt: str,
        start_frame: bytes,
        end_frame: bytes,
        duration: int,
        reference_images: List[bytes]
    ) -> bytes:
        """
        Generate video using VEO 3.1.

        Args:
            prompt: Video generation prompt
            start_frame: Start frame image data
            end_frame: End frame image data
            duration: Duration in seconds
            reference_images: List of character reference images

        Returns:
            Video data as bytes
        """
        # Build VEO 3.1 API request
        veo_params = {
            "prompt": prompt,
            "image": base64.b64encode(start_frame).decode(),
            "lastFrame": base64.b64encode(end_frame).decode(),
            "duration": duration,
            "aspectRatio": "16:9"
        }

        # Add reference images if present
        if reference_images:
            # CRITICAL: Must be exactly 8 seconds with references
            if duration != 8:
                raise ValueError(
                    f"Duration must be 8s when using reference images (got {duration}s)"
                )

            # Max 3 reference images
            if len(reference_images) > 3:
                raise ValueError(
                    f"Max 3 reference images allowed (got {len(reference_images)})"
                )

            veo_params["referenceImages"] = [
                base64.b64encode(img).decode()
                for img in reference_images
            ]
            veo_params["personGeneration"] = "allow_adult"

        # Call VEO 3.1 API (example - adjust for actual API)
        response = requests.post(
            "https://api.veo.google.com/v1/generate",
            headers={
                "Authorization": f"Bearer {self.veo_api_key}",
                "Content-Type": "application/json"
            },
            json=veo_params,
            timeout=180  # Video generation takes time
        )
        response.raise_for_status()

        # Wait for video to be ready and download
        result = response.json()
        video_url = result['video_url']

        import urllib.request
        with urllib.request.urlopen(video_url) as response:
            return response.read()

    def _stitch_videos(self, video_paths: List[Path]) -> Path:
        """
        Stitch scene videos together.

        Args:
            video_paths: List of scene video paths

        Returns:
            Path to stitched video
        """
        import subprocess

        # Create concat file for ffmpeg
        concat_file = self.output_dir / "concat.txt"
        with open(concat_file, 'w') as f:
            for video_path in video_paths:
                f.write(f"file '{video_path.absolute()}'\n")

        # Stitch with ffmpeg
        output_path = self.output_dir / "trailer_no_audio.mp4"
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(output_path)
        ], check=True)

        return output_path

    def _add_narration(self, video_path: Path, narration_text: str) -> Path:
        """
        Add narration audio to video.

        Args:
            video_path: Path to video
            narration_text: Narration script

        Returns:
            Path to final video with narration
        """
        # Generate narration audio with ElevenLabs
        import requests

        response = requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/voice_id",
            headers={
                "xi-api-key": self.elevenlabs_key
            },
            json={
                "text": narration_text,
                "model_id": "eleven_monolingual_v1"
            }
        )

        audio_path = self.output_dir / "narration.mp3"
        audio_path.write_bytes(response.content)

        # Mix audio with video
        import subprocess

        final_path = self.output_dir / "trailer_final.mp4"
        subprocess.run([
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first',
            '-c:v', 'copy',
            str(final_path)
        ], check=True)

        return final_path


# Usage Example
if __name__ == "__main__":
    import json

    # Load movie data
    with open('movie.json') as f:
        movie = json.load(f)

    # Create orchestrator
    orchestrator = TrailerOrchestrator(
        generator_url="http://localhost:8001",
        image_api_key="your_dalle_key",
        veo_api_key="your_veo_key"
    )

    # Generate trailer
    final_video = orchestrator.generate_trailer(movie)
    print(f"\n🎉 Trailer ready: {final_video}")
```

### Minimal Example (Core Logic Only)

```python
import requests

# 1. Get trailer breakdown
response = requests.post(
    "http://localhost:8001/generate-trailer",
    json={"movie": movie_data, "target_duration": 35}
)
trailer = response.json()['trailer']

# 2. Generate character reference images
character_refs = {}
for design in trailer['character_designs']:
    img = generate_image(design['image_generation_prompt'])
    character_refs[design['character_name']] = img

# 3. Generate scene videos
videos = []
for scene in trailer['scenes']:
    # Generate frames
    start_img = generate_image(scene['start_frame_prompt'])
    end_img = generate_image(scene['end_frame_prompt'])

    # Prepare VEO request
    veo_params = {
        "prompt": scene['video_prompt'],
        "image": start_img,
        "lastFrame": end_img,
        "duration": scene['duration_seconds'],
        "aspectRatio": "16:9"
    }

    # Add character references if present
    if scene['reference_images']:
        veo_params['referenceImages'] = [
            character_refs[name] for name in scene['reference_images']
        ]
        veo_params['personGeneration'] = "allow_adult"

    # Generate video
    video = call_veo_api(**veo_params)
    videos.append(video)

# 4. Stitch together
final_trailer = stitch_videos(videos)
```

---

## Error Handling

### Common Issues and Solutions

#### 1. Duration Mismatch

**Error:**
```
VEO Error: Duration must be 8 seconds when using referenceImages
```

**Cause:** Scene has `reference_images` but `duration_seconds != 8`

**Solution:**
```python
# Validation before calling VEO
if scene['reference_images'] and scene['duration_seconds'] != 8:
    raise ValueError(
        f"Scene {scene['scene_number']}: Duration must be 8s with references "
        f"(got {scene['duration_seconds']}s)"
    )
```

**Note:** The trailer generator validates this, but double-check in orchestrator.

#### 2. Too Many References

**Error:**
```
VEO Error: Maximum 3 reference images allowed
```

**Cause:** Scene has more than 3 reference images

**Solution:**
```python
if len(scene['reference_images']) > 3:
    # Take first 3 or raise error
    scene['reference_images'] = scene['reference_images'][:3]
    print(f"Warning: Scene {scene['scene_number']} has >3 refs, using first 3")
```

#### 3. Missing Character Reference

**Error:**
```
KeyError: 'Dr_Elara_Vance'
```

**Cause:** Scene references a character that wasn't generated

**Solution:**
```python
# Validate all references exist
for scene in trailer['scenes']:
    for char_name in scene['reference_images']:
        if char_name not in character_refs:
            raise ValueError(
                f"Scene {scene['scene_number']} references unknown character: {char_name}"
            )
```

#### 4. Image Generation Failed

**Error:**
```
DALL-E Error: Safety system triggered
```

**Cause:** Image prompt triggered content policy

**Solution:**
```python
try:
    img = generate_image(prompt)
except ContentPolicyError:
    # Log and skip, or use placeholder
    print(f"Warning: Image generation blocked for safety")
    img = load_placeholder_image()
```

---

## Best Practices

### 1. Caching

Cache generated images to avoid regeneration:

```python
import hashlib
from pathlib import Path

def generate_image_cached(prompt: str, cache_dir: Path) -> bytes:
    """Generate image with file-based caching."""
    # Hash prompt for cache key
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    cache_file = cache_dir / f"{prompt_hash}.png"

    # Check cache
    if cache_file.exists():
        print(f"  ✓ Using cached image: {cache_file.name}")
        return cache_file.read_bytes()

    # Generate new
    print(f"  Generating new image...")
    img_data = generate_image(prompt)

    # Cache for next time
    cache_file.write_bytes(img_data)

    return img_data
```

### 2. Parallel Processing

Generate character references in parallel:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_character_references_parallel(designs: List[dict]) -> Dict[str, str]:
    """Generate all character references in parallel."""
    character_refs = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        future_to_char = {
            executor.submit(generate_image, design['image_generation_prompt']): design['character_name']
            for design in designs
        }

        # Collect results
        for future in as_completed(future_to_char):
            char_name = future_to_char[future]
            try:
                img_data = future.result()
                character_refs[char_name] = img_data
                print(f"  ✓ Generated {char_name}")
            except Exception as e:
                print(f"  ✗ Failed {char_name}: {e}")
                raise

    return character_refs
```

### 3. Progress Tracking

Track progress for long-running operations:

```python
from tqdm import tqdm

def generate_scene_videos_with_progress(scenes, character_refs):
    """Generate scene videos with progress bar."""
    scene_videos = []

    with tqdm(total=len(scenes), desc="Generating scenes") as pbar:
        for scene in scenes:
            pbar.set_description(f"Scene {scene['scene_number']}")

            # Generate video...
            video = generate_scene_video(scene, character_refs)
            scene_videos.append(video)

            pbar.update(1)

    return scene_videos
```

### 4. Validation

Validate trailer breakdown before processing:

```python
def validate_trailer_breakdown(trailer: dict):
    """Validate trailer structure before processing."""

    # Check required fields
    required_fields = ['character_designs', 'scenes', 'technical_specs']
    for field in required_fields:
        if field not in trailer:
            raise ValueError(f"Missing required field: {field}")

    # Build set of available characters
    available_chars = {d['character_name'] for d in trailer['character_designs']}

    # Validate each scene
    for scene in trailer['scenes']:
        # Check duration constraint
        if scene['reference_images'] and scene['duration_seconds'] != 8:
            raise ValueError(
                f"Scene {scene['scene_number']}: Duration must be 8s with references"
            )

        # Check max references
        if len(scene['reference_images']) > 3:
            raise ValueError(
                f"Scene {scene['scene_number']}: Max 3 references (has {len(scene['reference_images'])})"
            )

        # Check references exist
        for char_name in scene['reference_images']:
            if char_name not in available_chars:
                raise ValueError(
                    f"Scene {scene['scene_number']}: Unknown character '{char_name}'"
                )

    print("✓ Trailer breakdown validated")
```

### 5. Error Recovery

Implement retry logic for API failures:

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=5):
    """Decorator to retry function on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"  ⚠️ Attempt {attempt + 1} failed: {e}")
                    print(f"  Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=10)
def generate_video_veo_with_retry(*args, **kwargs):
    """Generate VEO video with automatic retry."""
    return generate_video_veo(*args, **kwargs)
```

### 6. Logging

Comprehensive logging for debugging:

```python
import logging
from datetime import datetime

# Setup logging
log_file = f"trailer_generation_{datetime.now():%Y%m%d_%H%M%S}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Use in orchestrator
logger.info(f"Starting trailer generation for: {movie_title}")
logger.info(f"Character designs: {len(character_designs)}")
logger.info(f"Scenes: {len(scenes)}")

for scene in scenes:
    logger.info(f"Scene {scene['scene_number']}: {scene['scene_type']}")
    logger.debug(f"  Duration: {scene['duration_seconds']}s")
    logger.debug(f"  References: {scene['reference_images']}")
```

---

## Testing

### Test with Sample Data

```python
# Test trailer breakdown structure
def test_trailer_structure():
    """Test that trailer has expected structure."""
    response = requests.post(
        "http://localhost:8001/generate-trailer",
        json={"movie": sample_movie, "target_duration": 30}
    )
    trailer = response.json()['trailer']

    # Validate structure
    assert 'character_designs' in trailer
    assert 'scenes' in trailer
    assert 'technical_specs' in trailer

    # Validate character designs
    for design in trailer['character_designs']:
        assert 'character_name' in design
        assert 'image_generation_prompt' in design
        assert 'white background' in design['image_generation_prompt'].lower()
        assert 'brief_identifier' in design
        assert 'visual_style' in design

    # Validate scenes
    for scene in trailer['scenes']:
        assert 'reference_images' in scene
        assert isinstance(scene['reference_images'], list)

        if scene['reference_images']:
            # Scenes with references must be 8s
            assert scene['duration_seconds'] == 8
            # Max 3 references
            assert len(scene['reference_images']) <= 3

    print("✓ Trailer structure valid")

if __name__ == "__main__":
    test_trailer_structure()
```

---

## FAQ

### Q: Do I always need to use reference images?

**A:** No. Scenes without characters (`reference_images: []`) don't need them. Only character scenes use references.

### Q: Can I reuse reference images across multiple trailers?

**A:** Yes! If generating multiple trailers for the same movie, cache the character reference images and reuse them.

### Q: What if a character appears in 10 scenes?

**A:** No problem! That's the advantage of reference images - use the same character reference in all 10 scenes.

### Q: Can I mix aspect ratios?

**A:** Technically yes, but not recommended. VEO requires 16:9 with reference images, so keep all scenes 16:9 for consistency.

### Q: What if character generation fails?

**A:** Have a fallback strategy:
1. Retry with modified prompt
2. Use a placeholder/generic character
3. Skip character-focused scenes
4. Alert user and continue with available scenes

### Q: How long does generation take?

**A:** Approximate times:
- Trailer breakdown: 10-20 seconds (LLM)
- Character reference (each): 10-30 seconds (DALL-E/Flux)
- Scene video (each): 30-120 seconds (VEO 3.1)
- **Total for 5-scene trailer**: 5-15 minutes

---

## Support

For issues or questions:
- Check `REFERENCE_IMAGES_MIGRATION.md` for migration details
- Review `README.md` for service documentation
- Open GitHub issue with error logs

---

**Last Updated:** 2025-10-31
**Version:** 1.0.0 (Reference Images System)
