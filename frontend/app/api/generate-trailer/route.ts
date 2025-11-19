import { NextResponse } from "next/server";

import { sampleTrailerRequest } from "@/lib/data/sampleTrailerRequest";
import type { TrailerGenerationResponse } from "@/types/generation";

const VIDEO_GENERATOR_URL =
  process.env.VIDEO_GENERATOR_URL || "http://localhost:8000/generate/trailer";

interface IncomingPayload {
  character_designs?: unknown;
  scenes?: unknown;
  stitch_trailer?: boolean;
  image_api_key?: string;
  veo_api_key?: string;
  movie_title?: string;
  quizResults?: unknown;
}

export async function POST(request: Request) {
  let body: IncomingPayload = {};
  try {
    body = await request.json();
  } catch {
    // Ignore JSON parse errors and fall back to defaults
  }

  const payload = {
    character_designs:
      body.character_designs ?? sampleTrailerRequest.character_designs,
    scenes: body.scenes ?? sampleTrailerRequest.scenes,
    stitch_trailer: body.stitch_trailer ?? true,
    image_api_key: body.image_api_key,
    veo_api_key: body.veo_api_key,
  };

  try {
    const response = await fetch(VIDEO_GENERATOR_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        {
          error:
            errorText ||
            `Video generator returned status ${response.status.toString()}`,
        },
        { status: response.status },
      );
    }

    const data: TrailerGenerationResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unable to reach generator";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
