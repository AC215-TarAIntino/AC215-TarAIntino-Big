import { NextRequest, NextResponse } from "next/server";

const GCS_BUCKET_NAME = "tarantaino-output";
const GCS_PREFIX = "trailers";

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

    // Check if video exists in GCS bucket
    // We'll look for files matching the pattern: trailers/trailer_*{sessionId}*.mp4
    const videoUrl = await checkGCSForVideo(sessionId);

    if (videoUrl) {
      return NextResponse.json({
        status: "complete",
        sessionId,
        videoUrl,
        gcsUrl: `gs://${GCS_BUCKET_NAME}/${GCS_PREFIX}/${extractFilename(videoUrl)}`,
      });
    }

    // Video not found yet - still processing
    return NextResponse.json({
      status: "processing",
      sessionId,
      progress: 50, // Estimate - we don't have real progress tracking
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
    const publicUrl = `https://storage.googleapis.com/${GCS_BUCKET_NAME}/${GCS_PREFIX}/trailer_${sessionId}.mp4`;

    // Try to check if the file exists
    const headResponse = await fetch(publicUrl, { method: "HEAD" });
    if (headResponse.ok) {
      return publicUrl;
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
