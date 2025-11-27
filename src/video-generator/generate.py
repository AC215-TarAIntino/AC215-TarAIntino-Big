import time
from pathlib import Path

from google import genai
from google.cloud import storage
from google.genai import types

OUTPUT_DIR = Path("./output")

GCS_BUCKET_NAME = "tarantaino-output"
GCS_PREFIX = "video_generator_outputs"


def upload_to_gcs(local_path: Path, dest_path: str) -> None:
    """
    Upload a local file to the configured GCS bucket and make it publicly accessible.

    Args:
        local_path: Path to the file on disk (e.g. output/refs/char.png)
        dest_path:  Path inside the bucket (e.g. refs/char.png)
    """
    client = storage.Client()  # uses GOOGLE_APPLICATION_CREDENTIALS
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(f"{GCS_PREFIX}/{dest_path}" if GCS_PREFIX else dest_path)
    blob.upload_from_filename(str(local_path))

    # Make the blob publicly accessible so the frontend can display it
    try:
        blob.make_public()
        print(f"    ☁ Uploaded to gs://{GCS_BUCKET_NAME}/{blob.name} (public)")
    except Exception as e:
        print(f"    ☁ Uploaded to gs://{GCS_BUCKET_NAME}/{blob.name} (failed to make public: {e})")
        print("    ⚠️  You may need to enable public access on the bucket or use signed URLs")


def generate_character_references(
    image_api_key, character_designs: list[dict], session_id: str
) -> dict[str, str]:
    """
    Generate character reference images from designs.

    Args:
        character_designs: List of CharacterDesign objects
        session_id: Unique session ID for GCS organization

    Returns:
        Dict mapping character_name to image path
    """
    character_refs = {}

    for i, design in enumerate(character_designs, 1):
        char_name = design["character_name"]
        prompt = design["image_generation_prompt"]

        print(f"  [{i}/{len(character_designs)}] Generating {char_name}...")

        # Generate image using Gemini image model
        image_data, mime_type = generate_image(image_api_key, prompt)

        # Save image (determine extension from mime type)
        ext = "png" if "png" in mime_type else "jpg"
        image_path = OUTPUT_DIR / f"refs/{char_name}.{ext}"
        image_path.parent.mkdir(exist_ok=True, parents=True)
        image_path.write_bytes(image_data)

        # Upload with session ID in path for uniqueness
        upload_to_gcs(image_path, f"refs/{session_id}/{char_name}.{ext}")

        character_refs[char_name] = str(image_path)
        print(f"    ✓ Saved to {image_path}")

    return character_refs


def generate_scene_videos(
    image_api_key, veo_api_key, scenes: list[dict], character_refs: dict[str, str], session_id: str
) -> list[Path]:
    """
    Generate videos for all scenes.

    Args:
        scenes: List of scene objects
        character_refs: Dict of character_name -> image_path
        session_id: Unique session ID for GCS organization

    Returns:
        List of video file paths
    """
    scene_videos = []

    for scene in scenes:
        scene_num = scene["scene_number"]
        print(f"\n  Scene {scene_num}: {scene['scene_type']} ({scene['duration_seconds']}s)")

        # TESTING: Disable ALL frames for pure text-to-video mode
        start_img, start_mime = None, None
        end_img, end_mime = None, None
        print("    Testing pure text-to-video mode (no frames, no references)")

        # # NOTE: Veo 3.1 does not support combining frame interpolation with reference images
        # # We prioritize reference images for character consistency over frame control
        # # Therefore, we skip generating start/end frames when reference images are present

        # # Only generate frames if there are NO reference images
        # if not scene["reference_images"]:
        #     print(f"    Generating start frame...")
        #     start_img, start_mime = generate_image(image_api_key, scene["start_frame_prompt"])

        #     print(f"    Generating end frame...")
        #     end_img, end_mime = generate_image(image_api_key, scene["end_frame_prompt"])

        # Prepare reference images for this scene
        # TEMPORARILY DISABLED: Testing basic text-to-video mode first
        scene_ref_images = []
        scene_ref_mimes = []
        # if scene["reference_images"]:
        #     print(
        #         f"    Loading {len(scene['reference_images'])} character reference(s)..."
        #     )
        #     for char_name in scene["reference_images"]:
        #         ref_path = Path(character_refs[char_name])
        #         ref_bytes = ref_path.read_bytes()
        #         # Determine mime type from file extension
        #         ref_mime = "image/png" if ref_path.suffix == ".png" else "image/jpeg"
        #         scene_ref_images.append(ref_bytes)
        #         scene_ref_mimes.append(ref_mime)
        #         print(f"      ✓ {char_name}")
        print("    Testing basic text-to-video mode (no reference images)")

        # Call VEO 3.1
        print("    Generating video with VEO 3.1...")
        video_data = generate_video_veo(
            veo_api_key,
            prompt=scene["video_prompt"],
            start_frame=start_img,
            start_mime=start_mime,
            end_frame=end_img,
            end_mime=end_mime,
            duration=scene["duration_seconds"],
            reference_images=scene_ref_images,
            reference_mimes=scene_ref_mimes,
        )

        # Save video
        video_path = OUTPUT_DIR / f"scenes/scene_{scene_num:02d}.mp4"
        video_path.parent.mkdir(exist_ok=True, parents=True)
        video_path.write_bytes(video_data)

        # Upload with session ID in path for uniqueness
        upload_to_gcs(video_path, f"scenes/{session_id}/scene_{scene_num:02d}.mp4")

        scene_videos.append(video_path)
        print(f"    ✓ Saved to {video_path}")

    return scene_videos


def generate_image(image_api_key, prompt: str) -> tuple[bytes, str]:
    """
    Generate image using Gemini image model.

    Args:
        prompt: Image generation prompt

    Returns:
        Tuple of (image_bytes, mime_type)
    """

    client = genai.Client(api_key=image_api_key)
    response = client.models.generate_content(model="gemini-2.5-flash-image", contents=[prompt])

    # Access parts through the candidates
    if hasattr(response, "candidates") and response.candidates:
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(part.text)
            elif hasattr(part, "inline_data") and part.inline_data is not None:
                # Access the raw bytes and mime type from inline_data
                return part.inline_data.data, part.inline_data.mime_type

    raise ValueError("No image data found in response")


def generate_video_veo(
    veo_api_key,
    prompt: str,
    start_frame: bytes,
    start_mime: str,
    end_frame: bytes,
    end_mime: str,
    duration: int,
    reference_images: list[bytes],
    reference_mimes: list[str],
) -> bytes:
    """
    Generate video using VEO 3.1.

    Args:
        prompt: Video generation prompt
        start_frame: Start frame image data
        start_mime: Start frame MIME type
        end_frame: End frame image data
        end_mime: End frame MIME type
        duration: Duration in seconds
        reference_images: List of character reference image bytes
        reference_mimes: List of MIME types for reference images

    Returns:
        Video data as bytes
    """
    # Validate inputs for Veo 3.1
    # Valid durations: 4, 6, or 8 seconds (text-to-video or image-to-video)
    # CRITICAL: 8 seconds ONLY when using reference images
    valid_durations = [4, 6, 8]
    if duration not in valid_durations:
        raise ValueError(f"Duration must be 4, 6, or 8 seconds for Veo 3.1 (got {duration}s)")

    # Max 3 reference images
    if reference_images and len(reference_images) > 3:
        raise ValueError(f"Max 3 reference images allowed (got {len(reference_images)})")

    # Reference images REQUIRE 8 seconds (disabled for testing)
    # if reference_images and duration != 8:
    #     raise ValueError(
    #         f"Duration must be EXACTLY 8 seconds when using reference images (got {duration}s)"
    #     )

    # Initialize client
    client = genai.Client(api_key=veo_api_key)

    # Build config with reference images and end frame if provided
    config_params = {}

    # Add reference images for character consistency (max 3)
    if reference_images:
        ref_images = []
        for img_bytes, mime_type in zip(reference_images, reference_mimes, strict=True):
            img = types.Image(image_bytes=img_bytes, mime_type=mime_type)
            # Use "asset" reference type (as shown in Veo 3.1 docs)
            ref_img = types.VideoGenerationReferenceImage(image=img, reference_type="asset")
            ref_images.append(ref_img)
        config_params["reference_images"] = ref_images
        print(f"      [VEO 3.1] Using {len(ref_images)} character reference(s)")

    # Add end frame for interpolation (only if no reference images)
    # NOTE: Veo 3.1 does not support combining frame interpolation with reference images
    if end_frame and not reference_images:
        end_image = types.Image(image_bytes=end_frame, mime_type=end_mime)
        config_params["last_frame"] = end_image
        print("      [VEO 3.1] Using start and end frame interpolation")

    # Create config object
    config = types.GenerateVideosConfig(**config_params) if config_params else None

    # Convert start frame to Image type (passed directly, not in config)
    # Only use start frame if no reference images
    start_image = None
    if start_frame and not reference_images:
        start_image = types.Image(image_bytes=start_frame, mime_type=start_mime)
        print("      [VEO 3.1] Using start frame (image-to-video mode)")

    # Generate video using Veo 3.1 with full feature support
    print(f"      [VEO 3.1] Generating {duration}s video...")

    # Build kwargs - only include image and config if they're not None
    kwargs = {
        "model": "veo-3.0-fast-generate-001",
        "prompt": prompt,
    }
    if start_image is not None:
        kwargs["image"] = start_image
    if config is not None:
        kwargs["config"] = config

    operation = client.models.generate_videos(**kwargs)

    # Poll the operation status until the video is ready
    print("      [VEO] Video generation started, polling for completion...")
    while not operation.done:
        print("      [VEO] Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    print("      [VEO] Video generation complete!")

    # Download the generated video
    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video)

    # Return video bytes from the video object
    return generated_video.video.video_bytes


def stitch_videos(video_paths: list[Path], session_id: str) -> Path:
    """
    Stitch scene videos together.

    Args:
        video_paths: List of scene video paths
        session_id: Unique session ID for GCS organization

    Returns:
        Path to stitched video
    """
    import subprocess

    # Create concat file for ffmpeg
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for video_path in video_paths:
            f.write(f"file '{video_path.absolute()}'\n")

    # Stitch with ffmpeg
    output_path = OUTPUT_DIR / "trailer_no_audio.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output_path),
        ],
        check=True,
    )

    # Upload with session ID in path for uniqueness
    upload_to_gcs(output_path, f"trailers/{session_id}/{output_path.name}")

    return output_path
