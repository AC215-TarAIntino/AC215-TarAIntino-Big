/**
 * Video Service - Handles video generation status polling and retrieval
 *
 * TOGGLE BETWEEN MODES:
 * - USE_SIMPLE_TEST_MODE = true  → API-FREE: Instantly returns pre-existing video (no costs, no microservices)
 * - USE_SIMPLE_TEST_MODE = false → FULL PIPELINE: Runs all microservices + real Veo API (uses quota)
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:3000/api";

// 🎬 MODE SELECTOR: Toggle this to switch between simple test and full pipeline
// true  = API-FREE simple test mode (instant, no costs)
// false = FULL PIPELINE with all microservices + real Veo API
const USE_SIMPLE_TEST_MODE = false;  // Production mode with Claude Sonnet

export interface VideoStatus {
  status: "pending" | "processing" | "complete" | "error";
  progress?: number;
  videoUrl?: string;
  gcsUrl?: string;
  error?: string;
  sessionId: string;
}

export interface GenerateVideoRequest {
  sessionId: string;
  tasteVector: number[];
}

/**
 * Start video generation process
 */
export async function startVideoGeneration(
  sessionId: string,
  tasteVector: number[]
): Promise<{ success: boolean; message?: string; error?: string }> {
  try {
    // Use simple test mode to skip all backend processing
    const endpoint = USE_SIMPLE_TEST_MODE
      ? `${API_BASE_URL}/generate-video-simple`
      : `${API_BASE_URL}/generate-video`;

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ sessionId, tasteVector }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to start video generation:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

/**
 * Check video generation status
 */
export async function checkVideoStatus(
  sessionId: string
): Promise<VideoStatus> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/video-status?sessionId=${sessionId}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to check video status:", error);
    return {
      status: "error",
      sessionId,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

/**
 * Poll for video completion
 * Returns a promise that resolves when video is ready or rejects on error/timeout
 */
export async function pollForVideo(
  sessionId: string,
  options: {
    maxAttempts?: number;
    intervalMs?: number;
    onProgress?: (status: VideoStatus) => void;
  } = {}
): Promise<VideoStatus> {
  const {
    maxAttempts = 120, // 10 minutes at 5 second intervals
    intervalMs = 5000, // Check every 5 seconds
    onProgress,
  } = options;

  let attempts = 0;

  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await checkVideoStatus(sessionId);

        // Call progress callback
        if (onProgress) {
          onProgress(status);
        }

        // Check if complete
        if (status.status === "complete" && status.videoUrl) {
          resolve(status);
          return;
        }

        // Check if error
        if (status.status === "error") {
          reject(new Error(status.error || "Video generation failed"));
          return;
        }

        // Check timeout
        attempts++;
        if (attempts >= maxAttempts) {
          reject(
            new Error(
              "Timeout: Video generation took longer than expected. Please check back later."
            )
          );
          return;
        }

        // Continue polling
        setTimeout(poll, intervalMs);
      } catch (error) {
        reject(error);
      }
    };

    // Start polling
    poll();
  });
}
