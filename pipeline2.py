"""
Pipeline 2: Orchestration Function
Author: Robby

This module orchestrates all microservices to generate a complete movie trailer
from a taste vector. It handles the full pipeline from recommendation to video generation.

Flow:
    taste_vector -> recommendations -> movie concept -> trailer breakdown -> video -> GCS
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from google.cloud import storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaraintinoOrchestrator:
    """Orchestrates the full movie trailer generation pipeline."""

    def __init__(
        self,
        quiz_service_url: str = "http://localhost:8082",
        screenplay_service_url: str = "http://localhost:8080",
        scene_decomposer_url: str = "http://localhost:8001",
        video_generator_url: str = "http://localhost:8003",
        gcs_bucket_name: str = "tarantaino-output",
        gcp_project: Optional[str] = None,
        timeout: int = 300  # 5 minutes default timeout per service
    ):
        """
        Initialize the orchestrator with service URLs.

        Args:
            quiz_service_url: URL of the quiz-vector service
            screenplay_service_url: URL of the screenplay-writer service
            scene_decomposer_url: URL of the scene-decomposer service
            video_generator_url: URL of the video-generator service
            gcs_bucket_name: Name of the GCS bucket for final video storage
            gcp_project: Google Cloud project ID (reads from GOOGLE_CLOUD_PROJECT env if not provided)
            timeout: Timeout in seconds for HTTP requests
        """
        self.quiz_service_url = quiz_service_url.rstrip('/')
        self.screenplay_service_url = screenplay_service_url.rstrip('/')
        self.scene_decomposer_url = scene_decomposer_url.rstrip('/')
        self.video_generator_url = video_generator_url.rstrip('/')
        self.gcs_bucket_name = gcs_bucket_name
        self.timeout = timeout

        # Get GCP project from parameter or environment
        self.gcp_project = gcp_project or os.environ.get('GOOGLE_CLOUD_PROJECT')

        # Initialize GCS client lazily (only when needed)
        self._gcs_client = None

        logger.info("TaraintinoOrchestrator initialized")
        logger.info(f"  Quiz Service: {self.quiz_service_url}")
        logger.info(f"  Screenplay Writer: {self.screenplay_service_url}")
        logger.info(f"  Scene Decomposer: {self.scene_decomposer_url}")
        logger.info(f"  Video Generator: {self.video_generator_url}")
        logger.info(f"  GCS Bucket: {self.gcs_bucket_name}")
        if self.gcp_project:
            logger.info(f"  GCP Project: {self.gcp_project}")

    @property
    def gcs_client(self):
        """Lazy initialization of GCS client."""
        if self._gcs_client is None:
            if self.gcp_project:
                self._gcs_client = storage.Client(project=self.gcp_project)
            else:
                # Try to initialize without project (will use default from gcloud config)
                try:
                    self._gcs_client = storage.Client()
                except Exception as e:
                    logger.warning(f"Could not initialize GCS client: {e}")
                    logger.warning("GCS upload will not be available. Set GOOGLE_CLOUD_PROJECT or gcp_project parameter.")
        return self._gcs_client

    def check_services_health(self, skip_quiz_service: bool = False) -> Dict[str, bool]:
        """
        Check the health of all microservices.

        Args:
            skip_quiz_service: If True, don't check quiz-service health (optional for direct taste vector input)

        Returns:
            Dictionary mapping service names to health status (True/False)
        """
        services = {
            "screenplay-writer": f"{self.screenplay_service_url}/health",
            "scene-decomposer": f"{self.scene_decomposer_url}/health",
            "video-generator": f"{self.video_generator_url}/health",
        }

        # Only check quiz-service if needed
        if not skip_quiz_service:
            services["quiz-service"] = f"{self.quiz_service_url}/health"

        health_status = {}
        for service_name, health_url in services.items():
            try:
                response = requests.get(health_url, timeout=10)
                health_status[service_name] = response.status_code == 200
                logger.info(f"✓ {service_name}: {'healthy' if health_status[service_name] else 'unhealthy'}")
            except Exception as e:
                health_status[service_name] = False
                logger.error(f"✗ {service_name}: failed - {str(e)}")

        return health_status

    def get_movie_recommendations(
        self,
        taste_vector: List[float],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get movie recommendations based on taste vector.

        Args:
            taste_vector: User's taste vector from quiz
            top_n: Number of recommendations to retrieve

        Returns:
            List of recommended movies with metadata
        """
        logger.info(f"Step 1/5: Getting movie recommendations (top {top_n})")

        try:
            # Create a session ID (can be any unique identifier)
            session_id = f"orchestrator_{int(time.time())}"

            # Post taste vector to get recommendations
            payload = {
                "session_id": session_id,
                "taste_vector": taste_vector,
                "top_n": top_n
            }

            response = requests.post(
                f"{self.quiz_service_url}/recommend",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            recommendations = response.json()
            logger.info(f"✓ Received {len(recommendations.get('recommendations', []))} recommendations")
            return recommendations.get('recommendations', [])

        except Exception as e:
            logger.error(f"✗ Failed to get recommendations: {str(e)}")
            raise

    def generate_movie_concept(
        self,
        inspiration_movies: List[str],
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a new movie concept based on inspiration movies.

        Args:
            inspiration_movies: List of movie titles/IDs for inspiration
            custom_prompt: Optional custom prompt for movie generation

        Returns:
            Generated movie concept with all details
        """
        logger.info(f"Step 2/5: Generating movie concept")
        logger.info(f"  Inspiration: {', '.join(inspiration_movies[:3])}...")

        try:
            # Prepare payload with inspiration movies
            payload = {
                "movie_names": inspiration_movies if inspiration_movies else ["Inception", "The Matrix"]
            }

            # Add custom prompt if provided
            if custom_prompt:
                payload["custom_prompt"] = custom_prompt

            response = requests.post(
                f"{self.screenplay_service_url}/generate-movie",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            # The response might have a wrapper - check for 'movie' or 'data' key
            if 'movie' in result:
                movie_concept = result['movie']
            elif 'data' in result:
                movie_concept = result['data']
            else:
                movie_concept = result

            logger.info(f"✓ Generated movie: '{movie_concept.get('title', 'Unknown')}'")
            logger.info(f"  Genres: {', '.join(movie_concept.get('genres', []))}")

            # Debug: Log the first 500 chars of the response
            import json as j
            logger.debug(f"  Response structure: {j.dumps(result, indent=2)[:500]}")

            return movie_concept

        except Exception as e:
            logger.error(f"✗ Failed to generate movie concept: {str(e)}")
            raise

    def generate_trailer_breakdown(
        self,
        movie_concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate trailer breakdown with scenes and character designs.

        Args:
            movie_concept: Movie concept from screenplay-writer

        Returns:
            Trailer breakdown with scenes, character designs, and prompts
        """
        logger.info(f"Step 3/5: Generating trailer breakdown")

        try:
            payload = {
                "movie": movie_concept,  # Note: Using 'movie' not 'movie_data'
                "target_duration": 35,    # Note: Using 'target_duration' not 'trailer_duration'
                "include_narration": True
            }

            response = requests.post(
                f"{self.scene_decomposer_url}/generate-trailer",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            # The response has a 'trailer' key containing the actual breakdown
            trailer_breakdown = result.get('trailer', result)
            num_scenes = len(trailer_breakdown.get('scenes', []))
            num_characters = len(trailer_breakdown.get('character_designs', []))

            logger.info(f"✓ Generated trailer breakdown:")
            logger.info(f"  Scenes: {num_scenes}")
            logger.info(f"  Characters: {num_characters}")
            return trailer_breakdown

        except Exception as e:
            logger.error(f"✗ Failed to generate trailer breakdown: {str(e)}")
            raise

    def generate_video(
        self,
        trailer_breakdown: Dict[str, Any]
    ) -> str:
        """
        Generate the complete video from trailer breakdown.

        Args:
            trailer_breakdown: Trailer breakdown from scene-decomposer

        Returns:
            Local path to the generated video file
        """
        logger.info(f"Step 4/5: Generating video (this may take several minutes)")

        try:
            # Call the end-to-end trailer generation endpoint
            payload = {
                "character_designs": trailer_breakdown.get('character_designs', []),
                "scenes": trailer_breakdown.get('scenes', []),
                "api_key": "placeholder"  # This should be configured in the service
            }

            response = requests.post(
                f"{self.video_generator_url}/generate/trailer",
                json=payload,
                timeout=600  # 10 minutes for video generation
            )
            response.raise_for_status()

            result = response.json()
            video_path = result.get('final_video_path', '')

            logger.info(f"✓ Video generated successfully")
            logger.info(f"  Local path: {video_path}")
            return video_path

        except Exception as e:
            logger.error(f"✗ Failed to generate video: {str(e)}")
            raise

    def upload_to_gcs(
        self,
        local_video_path: str,
        destination_blob_name: Optional[str] = None
    ) -> str:
        """
        Upload the final video to Google Cloud Storage.

        Args:
            local_video_path: Path to the local video file
            destination_blob_name: Optional custom name in GCS

        Returns:
            Public URL of the uploaded video
        """
        logger.info(f"Step 5/5: Uploading video to GCS")

        try:
            # Generate destination name if not provided
            if not destination_blob_name:
                timestamp = int(time.time())
                destination_blob_name = f"trailers/trailer_{timestamp}.mp4"

            # Upload to GCS
            bucket = self.gcs_client.bucket(self.gcs_bucket_name)
            blob = bucket.blob(destination_blob_name)

            logger.info(f"  Uploading to gs://{self.gcs_bucket_name}/{destination_blob_name}")
            blob.upload_from_filename(local_video_path)

            # Make the blob publicly accessible (optional)
            # blob.make_public()

            # Generate public URL
            public_url = f"gs://{self.gcs_bucket_name}/{destination_blob_name}"

            logger.info(f"✓ Upload complete!")
            logger.info(f"  GCS URL: {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"✗ Failed to upload to GCS: {str(e)}")
            raise

    def generate_trailer_from_taste_vector(
        self,
        taste_vector: List[float],
        custom_prompt: Optional[str] = None,
        output_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main orchestration function: Generate a complete trailer from taste vector.

        This is the primary function that Robby's team should use. It handles the
        entire pipeline from taste vector to final video in GCS bucket.

        Args:
            taste_vector: User's taste vector from Karlo's quiz simulation
            custom_prompt: Optional custom prompt for movie generation
            output_name: Optional custom name for the output video in GCS

        Returns:
            Dictionary containing:
                - recommendations: List of recommended movies
                - movie_concept: Generated movie concept
                - trailer_breakdown: Scene breakdown
                - local_video_path: Path to generated video
                - gcs_url: URL of video in GCS bucket
                - success: Boolean indicating overall success
                - execution_time: Total time taken in seconds
        """
        start_time = time.time()

        logger.info("="*70)
        logger.info("STARTING TRAILER GENERATION PIPELINE")
        logger.info("="*70)

        result = {
            "success": False,
            "recommendations": None,
            "movie_concept": None,
            "trailer_breakdown": None,
            "local_video_path": None,
            "gcs_url": None,
            "execution_time": 0,
            "error": None
        }

        try:
            # Check service health (skip quiz-service since we have taste_vector directly)
            logger.info("\nChecking service health...")
            health_status = self.check_services_health(skip_quiz_service=True)
            unhealthy_services = [k for k, v in health_status.items() if not v]

            if unhealthy_services:
                error_msg = f"Unhealthy services: {', '.join(unhealthy_services)}"
                logger.error(f"✗ {error_msg}")
                result["error"] = error_msg
                return result

            logger.info("✓ All required services are healthy\n")

            # Step 1: Get recommendations
            # Note: For now, skipping the quiz-service recommendation step
            # since we're providing taste_vector directly. In production,
            # this would call get_movie_recommendations(taste_vector).
            logger.info("Step 1/5: Skipping recommendations (using direct taste vector)")
            recommendations = []
            result["recommendations"] = recommendations

            # Use generic inspiration since we don't have recommendations
            inspiration_movies = ["Pulp Fiction", "Reservoir Dogs", "Kill Bill"]

            # Step 2: Generate movie concept
            movie_concept = self.generate_movie_concept(
                inspiration_movies,
                custom_prompt
            )
            result["movie_concept"] = movie_concept

            # Step 3: Generate trailer breakdown
            trailer_breakdown = self.generate_trailer_breakdown(movie_concept)
            result["trailer_breakdown"] = trailer_breakdown

            # Step 4: Generate video
            local_video_path = self.generate_video(trailer_breakdown)
            result["local_video_path"] = local_video_path

            # Step 5: Upload to GCS
            gcs_url = self.upload_to_gcs(local_video_path, output_name)
            result["gcs_url"] = gcs_url

            # Success!
            result["success"] = True
            result["execution_time"] = time.time() - start_time

            logger.info("\n" + "="*70)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY! 🎬")
            logger.info("="*70)
            logger.info(f"Total execution time: {result['execution_time']:.2f} seconds")
            logger.info(f"Final video URL: {gcs_url}")
            logger.info("="*70 + "\n")

        except Exception as e:
            result["error"] = str(e)
            result["execution_time"] = time.time() - start_time
            logger.error(f"\n✗ Pipeline failed after {result['execution_time']:.2f} seconds")
            logger.error(f"Error: {str(e)}")

        return result


# Convenience function for easy usage
def generate_trailer(
    taste_vector: List[float],
    custom_prompt: Optional[str] = None,
    output_name: Optional[str] = None,
    **orchestrator_kwargs
) -> Dict[str, Any]:
    """
    Convenience function to generate a trailer from a taste vector.

    Args:
        taste_vector: User's taste vector from quiz
        custom_prompt: Optional custom prompt for movie generation
        output_name: Optional custom name for output video
        **orchestrator_kwargs: Additional arguments for TaraintinoOrchestrator

    Returns:
        Result dictionary from orchestrator

    Example:
        >>> taste_vector = [0.5, 0.3, 0.8, ...]  # From Karlo's pipeline1.py
        >>> result = generate_trailer(taste_vector)
        >>> if result['success']:
        ...     print(f"Video available at: {result['gcs_url']}")
    """
    orchestrator = TaraintinoOrchestrator(**orchestrator_kwargs)
    return orchestrator.generate_trailer_from_taste_vector(
        taste_vector,
        custom_prompt,
        output_name
    )


# Example usage
if __name__ == "__main__":
    # Example taste vector (this would come from Karlo's pipeline1.py)
    example_taste_vector = [0.5] * 1100  # Placeholder - 1100 dimensions

    # Generate trailer
    result = generate_trailer(
        taste_vector=example_taste_vector,
        custom_prompt="Create an epic sci-fi thriller with stunning visuals"
    )

    # Check result
    if result['success']:
        print(f"\n🎉 Success! Video URL: {result['gcs_url']}")
    else:
        print(f"\n❌ Failed: {result['error']}")
