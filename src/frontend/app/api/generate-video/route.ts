import { NextRequest, NextResponse } from "next/server";
import { videoStatusStore } from "@/lib/videoStatusStore";

const SCREENPLAY_WRITER_URL = "http://screenplay-writer:8000";
const SCENE_DECOMPOSER_URL = "http://scene-decomposer:8001";
const VIDEO_GENERATOR_URL = "http://video-generator:8003";
const QUIZ_SERVICE_URL = "http://quiz-service:8082";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { sessionId, tasteVector } = body;

    if (!sessionId || !tasteVector) {
      return NextResponse.json(
        { success: false, error: "Missing sessionId or tasteVector" },
        { status: 400 }
      );
    }

    // Start the async video generation process
    // We don't wait for it to complete - just trigger it
    generateVideoAsync(sessionId, tasteVector).catch((error) => {
      console.error("Video generation failed:", error);
    });

    return NextResponse.json({
      success: true,
      message: "Video generation started",
    });
  } catch (error) {
    console.error("Error starting video generation:", error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}

async function generateVideoAsync(sessionId: string, _tasteVector: number[]) {
  try {
    console.log(`[${sessionId}] Starting video generation...`);

    // Step 1: Get recommendations from taste vector
    console.log(`[${sessionId}] Getting recommendations...`);
    const recResponse = await fetch(`${QUIZ_SERVICE_URL}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, top_n: 5 }),
    });

    if (!recResponse.ok) {
      throw new Error("Failed to get recommendations");
    }

    const recommendations = await recResponse.json();

    // Step 2: Generate movie concept
    console.log(`[${sessionId}] Generating movie concept...`);

    // Extract movie titles from recommendations
    const movieNames = recommendations.recommendations
      ? recommendations.recommendations.map((rec: { title: string }) => rec.title)
      : recommendations.results?.map((rec: { title: string }) => rec.title) || [];

    console.log(`[${sessionId}] Using ${movieNames.length} movie recommendations:`, movieNames);

    const movieResponse = await fetch(`${SCREENPLAY_WRITER_URL}/generate-movie`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        movie_names: movieNames.slice(0, 5), // Use top 5 movies
      }),
    });

    if (!movieResponse.ok) {
      const errorText = await movieResponse.text();
      console.error(`[${sessionId}] Screenplay-writer error:`, errorText);
      throw new Error(`Failed to generate movie: ${errorText}`);
    }

    const movieData = await movieResponse.json();

    if (!movieData.success || !movieData.movie) {
      throw new Error(`Failed to generate movie: ${movieData.error || "Unknown error"}`);
    }

    const movie = movieData.movie;

    console.log(`[${sessionId}] Movie generated: ${movie.title}`);

    // Save movie title for the result page
    const movieTitle = movie.title || movie.name || "Untitled Movie";

    // Step 3: Generate trailer breakdown
    console.log(`[${sessionId}] Generating trailer breakdown...`);
    const trailerResponse = await fetch(`${SCENE_DECOMPOSER_URL}/generate-trailer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        movie: movie,
        target_duration: 35,
        include_narration: true,
      }),
    });

    if (!trailerResponse.ok) {
      throw new Error("Failed to generate trailer breakdown");
    }

    const trailerData = await trailerResponse.json();

    if (!trailerData.success || !trailerData.trailer) {
      console.error(`[${sessionId}] Scene-decomposer error:`, trailerData.error);
      throw new Error(`Failed to generate trailer breakdown: ${trailerData.error || "Unknown error"}`);
    }

    const trailer = trailerData.trailer;
    console.log(`[${sessionId}] Trailer breakdown generated: ${trailer.scenes.length} scenes`);

    // Step 4: Generate video (REAL MODE - using VEO 3.0 Fast Generate)
    console.log(`[${sessionId}] Starting video generation (REAL MODE - using VEO 3.0 Fast)...`);
    const videoResponse = await fetch(`${VIDEO_GENERATOR_URL}/generate/trailer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        character_designs: trailer.character_designs,
        scenes: trailer.scenes,
        stitch_trailer: true,
      }),
      // @ts-expect-error - Node.js fetch (undici) supports these options
      headersTimeout: 1200000, // 20 minutes
      bodyTimeout: 1200000,    // 20 minutes
    });

    if (!videoResponse.ok) {
      throw new Error("Failed to generate video");
    }

    const videoData = await videoResponse.json();

    console.log(`[${sessionId}] Video generation complete!`);
    console.log(`[${sessionId}] GCS URL: ${videoData.gcs_url}`);
    console.log(`[${sessionId}] Public URL: ${videoData.public_url}`);

    // Store the result in memory so the status endpoint can find it
    videoStatusStore.set(sessionId, {
      status: "complete",
      gcsUrl: videoData.gcs_url,
      publicUrl: videoData.public_url,
      movieTitle: movieTitle,
      progress: 100,
    });

    return videoData;
  } catch (error) {
    console.error(`[${sessionId}] Video generation failed:`, error);
    throw error;
  }
}
