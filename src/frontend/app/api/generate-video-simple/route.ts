import { NextRequest, NextResponse } from "next/server";
import { videoStatusStore } from "@/lib/videoStatusStore";

/**
 * ULTRA-SIMPLE TEST MODE
 * Immediately returns success with a pre-existing GCS video
 * NO API calls, NO LLMs, NO video generation
 * Just for testing the frontend flow
 */

const VIDEO_GENERATOR_URL = "http://video-generator:8003";
const EXISTING_GCS_URL = "gs://taraintino-showcase-videos/video_generator_outputs/trailers/trailer_no_audio.mp4";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { sessionId } = body;

    if (!sessionId) {
      return NextResponse.json(
        { success: false, error: "Missing sessionId" },
        { status: 400 }
      );
    }

    console.log(`[${sessionId}] 🧪 SIMPLE TEST MODE: Getting signed URL for existing video`);

    // Call video-generator to get a signed URL for the existing video
    let signedUrl = "";
    try {
      const response = await fetch(`${VIDEO_GENERATOR_URL}/signed-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gcs_path: "video_generator_outputs/trailers/trailer_no_audio.mp4",
        }),
      });

      if (response.ok) {
        const data = await response.json();
        signedUrl = data.signed_url;
        console.log(`[${sessionId}] ✅ Got signed URL`);
      } else {
        console.error(`[${sessionId}] Failed to get signed URL, using direct URL (may not work)`);
        signedUrl = "https://storage.googleapis.com/taraintino-showcase-videos/video_generator_outputs/trailers/trailer_no_audio.mp4";
      }
    } catch (error) {
      console.error(`[${sessionId}] Error getting signed URL:`, error);
      signedUrl = "https://storage.googleapis.com/taraintino-showcase-videos/video_generator_outputs/trailers/trailer_no_audio.mp4";
    }

    // Immediately store the "completed" status
    videoStatusStore.set(sessionId, {
      status: "complete",
      gcsUrl: EXISTING_GCS_URL,
      publicUrl: signedUrl,
      progress: 100,
    });

    console.log(`[${sessionId}] ✅ Status stored, frontend should transition now`);

    return NextResponse.json({
      success: true,
      message: "Test mode: Using existing video",
      gcsUrl: EXISTING_GCS_URL,
      publicUrl: signedUrl,
    });
  } catch (error) {
    console.error("Error in simple test mode:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
