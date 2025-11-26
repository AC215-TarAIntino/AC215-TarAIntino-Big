"""
FastAPI application for the movie pipeline.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .schemas import MovieRequest, MovieGenerationResponse, GeneratedMovie
from .movie_fetcher import MovieFetcher, MovieFetcherError
from .movie_generator import MovieGenerator, MovieGeneratorError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    logger.info("Starting Movie Pipeline API")
    logger.info(f"Using OpenRouter model: {settings.openrouter_model}")
    yield
    logger.info("Shutting down Movie Pipeline API")


# Create FastAPI app
app = FastAPI(
    title="Movie Pipeline API",
    description="Generate movie concepts inspired by existing movies using OMDb and OpenRouter",
    version="0.1.0",
    lifespan=lifespan
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
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Movie Pipeline API",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "omdb_configured": bool(settings.omdb_api_key),
        "openrouter_configured": bool(settings.openrouter_api_key),
        "model": settings.openrouter_model
    }


@app.post("/generate-movie", response_model=MovieGenerationResponse)
async def generate_movie(request: MovieRequest):
    """
    Generate a new movie concept based on provided movie names.

    Args:
        request: MovieRequest with list of movie names

    Returns:
        MovieGenerationResponse with generated movie details
    """
    logger.info(f"Received request to generate movie from: {request.movie_names}")

    try:
        # Initialize fetcher and generator
        fetcher = MovieFetcher()
        generator = MovieGenerator()

        # Fetch movie data from OMDb
        logger.info("Fetching movie data from OMDb...")
        movies = fetcher.fetch_multiple_movies(request.movie_names)

        if not movies:
            raise HTTPException(
                status_code=404,
                detail=f"None of the provided movies were found in OMDb: {request.movie_names}"
            )

        logger.info(f"Found {len(movies)} movies out of {len(request.movie_names)} requested")

        # Generate new movie concept
        logger.info("Generating movie concept with LLM...")
        generated_movie = generator.generate_from_movies(
            movies=movies,
            model_override=request.model
        )

        logger.info(f"Successfully generated movie: {generated_movie.title}")

        # Return response
        return MovieGenerationResponse(
            success=True,
            movie=generated_movie,
            input_movies_found=len(movies),
            input_movies_data=movies,
            model_used=request.model or settings.openrouter_model
        )

    except MovieFetcherError as e:
        logger.error(f"Movie fetcher error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch movie data: {str(e)}")

    except MovieGeneratorError as e:
        logger.error(f"Movie generator error: {e}")
        return MovieGenerationResponse(
            success=False,
            movie=None,
            input_movies_found=len(movies) if 'movies' in locals() else 0,
            error=str(e),
            model_used=request.model or settings.openrouter_model
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/fetch-movie-data")
async def fetch_movie_data(movie_names: list[str]):
    """
    Fetch raw movie data from OMDb without generating a new movie.

    Useful for testing and debugging.

    Args:
        movie_names: List of movie names to fetch

    Returns:
        Dictionary with fetched movies
    """
    logger.info(f"Fetching data for movies: {movie_names}")

    try:
        fetcher = MovieFetcher()
        movies = fetcher.fetch_multiple_movies(movie_names)

        return {
            "success": True,
            "movies_found": len(movies),
            "movies": movies
        }

    except Exception as e:
        logger.error(f"Error fetching movies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "movie_pipeline.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
