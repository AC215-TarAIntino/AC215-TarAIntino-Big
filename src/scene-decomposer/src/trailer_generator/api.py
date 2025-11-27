"""
FastAPI application for the trailer generator.
"""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .scene_analyzer import MovieAnalyzer
from .scene_generator import SceneGenerator, SceneGeneratorError
from .schemas import (
    GeneratedMovie,
    MovieAnalysis,
    TrailerGenerationResponse,
    TrailerRequest,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    logger.info("Starting Trailer Generator API")
    logger.info(f"Using OpenRouter model: {settings.openrouter_model}")
    logger.info(f"Default trailer duration: {settings.default_trailer_duration}s")

    # Ensure outputs directory exists
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    yield
    logger.info("Shutting down Trailer Generator API")


# Create FastAPI app
app = FastAPI(
    title="Trailer Generator API",
    description="Generate detailed trailer scene breakdowns from movie descriptions using AI",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Trailer Generator API",
        "version": "0.1.0",
        "status": "healthy",
        "endpoints": {
            "generate_trailer": "/generate-trailer",
            "analyze_movie": "/analyze-movie",
            "health": "/health",
        },
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "openrouter_configured": bool(settings.openrouter_api_key),
        "model": settings.openrouter_model,
        "default_duration": settings.default_trailer_duration,
        "include_narration": settings.include_narration,
    }


@app.post("/generate-trailer", response_model=TrailerGenerationResponse)
async def generate_trailer(request: TrailerRequest):
    """
    Generate a detailed trailer scene breakdown from a movie description.

    This endpoint takes a complete movie description and generates a scene-by-scene
    breakdown ready for video generation with VEO 3.1 and image generation with
    DALL-E/Flux.

    Args:
        request: TrailerRequest with movie data and parameters

    Returns:
        TrailerGenerationResponse with detailed scene breakdown
    """
    logger.info(f"Received request to generate trailer for: {request.movie.title}")
    logger.info(
        f"Target duration: {request.target_duration}s, Narration: {request.include_narration}"
    )

    start_time = time.time()

    try:
        # Initialize scene generator
        generator = SceneGenerator()

        # Generate trailer breakdown
        logger.info("Generating trailer scene breakdown with LLM...")
        trailer = generator.generate_trailer(
            movie=request.movie,
            target_duration=request.target_duration,
            include_narration=request.include_narration,
            model_override=request.model,
        )

        generation_time = time.time() - start_time
        logger.info(
            f"Successfully generated trailer with {len(trailer.scenes)} scenes in {generation_time:.2f}s"
        )

        # Save to outputs folder
        output_path = (
            Path("outputs") / f"{request.movie.title.replace(' ', '_').lower()}_trailer.json"
        )
        try:
            import json

            with open(output_path, "w") as f:
                json.dump(trailer.model_dump(), f, indent=2)
            logger.info(f"Saved trailer breakdown to: {output_path}")
        except Exception as e:
            logger.warning(f"Failed to save output file: {e}")

        # Return response
        return TrailerGenerationResponse(
            success=True,
            trailer=trailer,
            error=None,
            model_used=request.model or settings.openrouter_model,
            generation_time_seconds=generation_time,
        )

    except SceneGeneratorError as e:
        logger.error(f"Scene generator error: {e}")
        return TrailerGenerationResponse(
            success=False,
            trailer=None,
            error=str(e),
            model_used=request.model or settings.openrouter_model,
            generation_time_seconds=time.time() - start_time,
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@app.post("/analyze-movie", response_model=MovieAnalysis)
async def analyze_movie(movie: GeneratedMovie):
    """
    Analyze a movie to extract key information for trailer generation.

    This is a utility endpoint that can be used to preview what information
    will be extracted from a movie before generating the full trailer.

    Args:
        movie: GeneratedMovie object

    Returns:
        MovieAnalysis with extracted information
    """
    logger.info(f"Analyzing movie: {movie.title}")

    try:
        analyzer = MovieAnalyzer(movie)
        analysis = analyzer.analyze()

        logger.info(
            f"Analysis complete: {len(analysis.main_characters)} characters, {len(analysis.key_themes)} themes"
        )

        return analysis

    except Exception as e:
        logger.error(f"Error analyzing movie: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze movie: {str(e)}") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "trailer_generator.api:app", host=settings.api_host, port=settings.api_port, reload=True
    )
