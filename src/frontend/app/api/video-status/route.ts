import { NextRequest, NextResponse } from "next/server";
import { videoStatusStore } from "@/lib/videoStatusStore";

const GCS_BUCKET_NAME = "taraintino-showcase-videos";
const GCS_PREFIX = "video_generator_outputs/trailers";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const sessionId = searchParams.get("sessionId");

    if (!sessionId) {
      return NextResponse.json(
        { error: "Missing sessionId parameter" },
        { status: 400 }
      );
    }

    // Check in-memory store first (this is set only when the FULL pipeline completes)
    const storedStatus = videoStatusStore.get(sessionId);
    if (storedStatus && storedStatus.status === "complete" && storedStatus.publicUrl) {
      return NextResponse.json({
        status: "complete",
        sessionId,
        videoUrl: storedStatus.publicUrl,
        gcsUrl: storedStatus.gcsUrl,
        movieTitle: storedStatus.movieTitle,
        progress: 100,
      });
    }

    // If not in store yet, the pipeline is still running
    // Don't check GCS yet - wait for the backend to complete the full pipeline
    // This prevents showing "complete" before screenplay/scene-decomposer finish
    return NextResponse.json({
      status: "processing",
      sessionId,
      progress: 50,
    });
  } catch (error) {
    console.error("Error checking video status:", error);
    return NextResponse.json(
      {
        status: "error",
        sessionId: request.nextUrl.searchParams.get("sessionId") || "unknown",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}

async function checkGCSForVideo(sessionId: string): Promise<string | null> {
  try {
    // In a real implementation, you would use the GCS API to list files
    // For now, we'll construct a predictable URL based on the session ID
    // This assumes your video generator uploads with a naming convention

    // Option 1: Direct API call to video-generator to check status
    const VIDEO_GENERATOR_URL = "http://video-generator:8003";

    try {
      const response = await fetch(`${VIDEO_GENERATOR_URL}/status/${sessionId}`, {
        method: "GET",
      });

      if (response.ok) {
        const data = await response.json();
        if (data.videoUrl || data.gcs_url) {
          // Convert GCS URL to public URL if needed
          return convertGCSToPublicURL(data.gcs_url || data.videoUrl);
        }
      }
    } catch (error) {
      // Video generator might not have a status endpoint
      console.log("Video generator status check failed, will try GCS polling");
    }

    // Option 2: Construct expected URL based on timestamp/session
    // This is a fallback if the video generator doesn't track status
    const gcsPath = `${GCS_PREFIX}/${sessionId}/trailer_no_audio.mp4`;
    const publicUrl = `https://storage.googleapis.com/${GCS_BUCKET_NAME}/${gcsPath}`;

    // Try to check if the file exists (may fail if not public)
    const headResponse = await fetch(publicUrl, { method: "HEAD" });
    if (headResponse.ok) {
      return publicUrl;
    }

    // If public access fails, try to generate a signed URL
    try {
      const signedUrlResponse = await fetch(`${VIDEO_GENERATOR_URL}/signed-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gcs_path: gcsPath,
          expiration_minutes: 120, // 2 hour expiration
        }),
      });

      if (signedUrlResponse.ok) {
        const signedData = await signedUrlResponse.json();
        return signedData.signed_url;
      }
    } catch (signedUrlError) {
      console.log("Failed to generate signed URL:", signedUrlError);
    }

    return null;
  } catch (error) {
    console.error("Error checking GCS:", error);
    return null;
  }
}

function convertGCSToPublicURL(gcsUrl: string): string {
  // Convert gs://bucket/path to https://storage.googleapis.com/bucket/path
  if (gcsUrl.startsWith("gs://")) {
    return gcsUrl.replace("gs://", "https://storage.googleapis.com/");
  }
  return gcsUrl;
}

function extractFilename(url: string): string {
  return url.split("/").pop() || "";
}
