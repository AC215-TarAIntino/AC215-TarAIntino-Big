import { NextRequest, NextResponse } from "next/server";

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

async function generateVideoAsync(sessionId: string, tasteVector: number[]) {
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

    // Step 4: Generate video
    console.log(`[${sessionId}] Starting video generation (this may take 5-15 minutes)...`);
    const videoResponse = await fetch(`${VIDEO_GENERATOR_URL}/generate/trailer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        character_designs: trailer.character_designs,
        scenes: trailer.scenes,
        stitch_trailer: true,
      }),
    });

    if (!videoResponse.ok) {
      throw new Error("Failed to generate video");
    }

    const videoData = await videoResponse.json();

    console.log(`[${sessionId}] Video generation complete!`);
    console.log(`[${sessionId}] GCS URL: ${videoData.gcs_url}`);

    // Store the result (in production, use a database)
    // For now, we'll rely on the client polling GCS directly
    return videoData;
  } catch (error) {
    console.error(`[${sessionId}] Video generation failed:`, error);
    throw error;
  }
}
