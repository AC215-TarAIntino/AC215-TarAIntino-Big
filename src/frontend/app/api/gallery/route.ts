import { NextRequest, NextResponse } from "next/server";

const GCS_BUCKET_NAME = "taraintino-showcase-videos";
const GALLERY_MANIFEST_PATH = "gallery/gallery_manifest.json";

interface Movie {
  title: string;
  duration: number;
  narration: string;
  scenes_count: number;
  characters: string[];
  visual_style: string;
  aspect_ratio: string;
  created_at: string;
  filename: string;
  video_url: string;
  thumbnail_url: string;
}

interface GalleryManifest {
  version: string;
  created_at: string;
  total_movies: number;
  movies: Movie[];
}

export async function GET(request: NextRequest) {
  try {
    // Fetch the gallery manifest from GCS
    const manifestUrl = `https://storage.googleapis.com/${GCS_BUCKET_NAME}/${GALLERY_MANIFEST_PATH}`;

    const response = await fetch(manifestUrl, {
      headers: {
        "Cache-Control": "no-cache",
      },
    });

    if (!response.ok) {
      console.error("Failed to fetch gallery manifest:", response.status);
      return NextResponse.json(
        { error: "Failed to fetch gallery data" },
        { status: 500 }
      );
    }

    const manifest: GalleryManifest = await response.json();

    // Convert GCS URLs to signed URLs if needed, or return as-is
    // For now, we'll return the manifest as-is and handle URL signing on the frontend if needed

    return NextResponse.json({
      success: true,
      data: manifest,
    });
  } catch (error) {
    console.error("Error fetching gallery:", error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
