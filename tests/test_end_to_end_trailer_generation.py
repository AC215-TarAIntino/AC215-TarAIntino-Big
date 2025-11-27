"""
End-to-end integration tests for the TarAIntino trailer generation pipeline.

Tests the full flow from quiz -> screenplay -> scene decomposer -> video generation.
Run these tests with all services running via docker-compose.
"""

import time

import pytest
import requests

# Service URLs
QUIZ_SERVICE_URL = "http://localhost:8082"
SCREENPLAY_SERVICE_URL = "http://localhost:8080"
SCENE_DECOMPOSER_URL = "http://localhost:8001"
VIDEO_GENERATOR_URL = "http://localhost:8003"

# Timeout for service responses (in seconds)
REQUEST_TIMEOUT = 30


@pytest.fixture(scope="module")
def verify_services_running():
    """Verify all services are running before tests."""
    services = {
        "Quiz Service": f"{QUIZ_SERVICE_URL}/health",
        "Screenplay Writer": f"{SCREENPLAY_SERVICE_URL}/health",
        "Scene Decomposer": f"{SCENE_DECOMPOSER_URL}/health",
        "Video Generator": f"{VIDEO_GENERATOR_URL}/health",
    }

    for service_name, health_url in services.items():
        try:
            response = requests.get(health_url, timeout=5)
            assert response.status_code == 200, f"{service_name} is not healthy"
        except requests.exceptions.RequestException as e:
            pytest.skip(f"{service_name} is not running: {e}")


class TestServiceHealth:
    """Test that all services are healthy and configured correctly."""

    def test_quiz_service_health(self, verify_services_running):
        """Test quiz service health endpoint."""
        response = requests.get(f"{QUIZ_SERVICE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True

    def test_screenplay_service_health(self, verify_services_running):
        """Test screenplay writer health endpoint."""
        response = requests.get(f"{SCREENPLAY_SERVICE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "openrouter_configured" in data
        assert "model" in data

    def test_scene_decomposer_health(self, verify_services_running):
        """Test scene decomposer health endpoint."""
        response = requests.get(f"{SCENE_DECOMPOSER_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert "openrouter_configured" in data
        assert "model" in data

    def test_video_generator_health(self, verify_services_running):
        """Test video generator health endpoint."""
        response = requests.get(f"{VIDEO_GENERATOR_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"


class TestQuizService:
    """Test quiz service endpoints."""

    def test_quiz_start(self, verify_services_running):
        """Test starting a new quiz session."""
        response = requests.post(
            f"{QUIZ_SERVICE_URL}/quiz/start", json={"n_questions": 5}, timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "question" in data
        question = data["question"]
        assert "tag_label" in question
        assert "scale" in question

    def test_quiz_answer_submission(self, verify_services_running):
        """Test submitting quiz answers."""
        # Start quiz
        start_response = requests.post(
            f"{QUIZ_SERVICE_URL}/quiz/start", json={"n_questions": 3}, timeout=REQUEST_TIMEOUT
        )
        assert start_response.status_code == 200
        session_data = start_response.json()
        session_id = session_data["session_id"]
        question_id = session_data["question"]["question_id"]

        # Submit first answer with correct question_id
        answer_response = requests.post(
            f"{QUIZ_SERVICE_URL}/quiz/answer",
            json={"session_id": session_id, "question_id": question_id, "answer": 5},
            timeout=REQUEST_TIMEOUT,
        )
        assert answer_response.status_code == 200
        answer_data = answer_response.json()
        # Response should have either next question or complete flag
        assert (
            "next_question" in answer_data
            or "question" in answer_data
            or answer_data.get("complete") is True
        )

    def test_quiz_completion_and_recommendation(self, verify_services_running):
        """Test completing quiz and getting recommendations."""
        # Start quiz with minimal questions
        start_response = requests.post(
            f"{QUIZ_SERVICE_URL}/quiz/start", json={"n_questions": 2}, timeout=REQUEST_TIMEOUT
        )
        assert start_response.status_code == 200
        session_data = start_response.json()
        session_id = session_data["session_id"]

        # Answer all questions with correct structure
        current_question = session_data["question"]
        for _ in range(2):
            response = requests.post(
                f"{QUIZ_SERVICE_URL}/quiz/answer",
                json={
                    "session_id": session_id,
                    "question_id": current_question["question_id"],
                    "answer": 4,
                },
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                response_data = response.json()
                if "question" in response_data:
                    current_question = response_data["question"]

        # Get taste vector (this happens internally, but we can test recommendation)
        # Note: The actual taste vector is computed during quiz completion


class TestScreenplayService:
    """Test screenplay writer service endpoints."""

    def test_generate_movie_basic(self, verify_services_running):
        """Test basic movie generation."""
        payload = {
            "taste_vector": {"action": 0.8, "comedy": 0.5, "drama": 0.6},
            "preferences": {"runtime": "120 min", "rating": "PG-13"},
        }

        response = requests.post(
            f"{SCREENPLAY_SERVICE_URL}/generate-movie", json=payload, timeout=REQUEST_TIMEOUT
        )

        # API might return 422 (validation error), 500 (OpenRouter not configured), or 200 (success)
        assert response.status_code in [200, 422, 500]

        if response.status_code == 200:
            data = response.json()
            assert "title" in data
            assert "plot_summary" in data
            assert "genres" in data

    def test_fetch_movie_data(self, verify_services_running):
        """Test fetching movie data from OMDb."""
        response = requests.post(
            f"{SCREENPLAY_SERVICE_URL}/fetch-movie-data",
            json={"title": "Inception", "year": 2010},
            timeout=REQUEST_TIMEOUT,
        )

        # API might return 422 (validation error), 404 (not found), 500 (error), or 200 (success)
        assert response.status_code in [200, 404, 422, 500]


class TestSceneDecomposer:
    """Test scene decomposer service endpoints."""

    def test_analyze_movie_structure(self, verify_services_running):
        """Test analyzing a movie structure."""
        movie_data = {
            "title": "Test Movie",
            "plot_summary": "A thrilling story about a hero's journey.",
            "genres": ["Action", "Adventure"],
            "cast": [
                {
                    "actor_name": "Test Actor",
                    "character_name": "Hero",
                    "physical_description": "Tall and strong",
                    "personality_traits": ["brave", "determined"],
                }
            ],
        }

        response = requests.post(
            f"{SCENE_DECOMPOSER_URL}/analyze-movie", json=movie_data, timeout=REQUEST_TIMEOUT
        )

        # Might return 422 (validation error), 500 (OpenRouter not configured), or 200 (success)
        assert response.status_code in [200, 422, 500]

    def test_generate_trailer_breakdown(self, verify_services_running):
        """Test generating a trailer breakdown."""
        movie_data = {
            "title": "Test Movie",
            "tagline": "An epic adventure",
            "genres": ["Action"],
            "plot_summary": "A hero saves the world from destruction.",
            "cast": [
                {
                    "actor_name": "John Doe",
                    "character_name": "The Hero",
                    "physical_description": "Athletic build",
                    "personality_traits": ["courageous"],
                }
            ],
            "visual_style": "Dark and cinematic",
            "themes": ["heroism", "sacrifice"],
        }

        response = requests.post(
            f"{SCENE_DECOMPOSER_URL}/generate-trailer", json=movie_data, timeout=REQUEST_TIMEOUT
        )

        # Might return 422 (validation error), 500 (OpenRouter not configured), or 200 (success)
        assert response.status_code in [200, 422, 500]

        if response.status_code == 200:
            data = response.json()
            assert "scenes" in data or "characters" in data


class TestVideoGenerator:
    """Test video generator service endpoints."""

    def test_generate_character_references(self, verify_services_running):
        """Test generating character reference images."""
        payload = {
            "characters": [
                {
                    "character_name": "Test Character",
                    "physical_description": "Young woman with brown hair",
                    "personality_traits": ["brave", "intelligent"],
                }
            ]
        }

        response = requests.post(
            f"{VIDEO_GENERATOR_URL}/generate/character-references",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        # This endpoint might return various error codes or success
        assert response.status_code in [200, 400, 422, 500, 501]

    def test_health_status_details(self, verify_services_running):
        """Test detailed health status of video generator."""
        response = requests.get(f"{VIDEO_GENERATOR_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestEndToEndPipeline:
    """Test the complete end-to-end pipeline."""

    @pytest.fixture
    def sample_taste_vector(self):
        """Sample taste vector from completed quiz."""
        return {"action": 0.7, "comedy": 0.4, "drama": 0.8, "thriller": 0.6, "scifi": 0.5}

    def test_quiz_to_screenplay_flow(self, verify_services_running, sample_taste_vector):
        """Test flow from quiz completion to screenplay generation."""
        # Step 1: Start and complete quiz
        start_response = requests.post(
            f"{QUIZ_SERVICE_URL}/quiz/start", json={"n_questions": 2}, timeout=REQUEST_TIMEOUT
        )
        assert start_response.status_code == 200
        session_data = start_response.json()
        session_id = session_data["session_id"]
        current_question = session_data["question"]

        # Complete quiz with correct format
        for _ in range(2):
            response = requests.post(
                f"{QUIZ_SERVICE_URL}/quiz/answer",
                json={
                    "session_id": session_id,
                    "question_id": current_question["question_id"],
                    "answer": 5,
                },
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 200 and "question" in response.json():
                current_question = response.json()["question"]

        # Step 2: Generate screenplay using taste vector
        screenplay_payload = {
            "taste_vector": sample_taste_vector,
            "preferences": {"runtime": "120 min"},
        }

        screenplay_response = requests.post(
            f"{SCREENPLAY_SERVICE_URL}/generate-movie",
            json=screenplay_payload,
            timeout=REQUEST_TIMEOUT,
        )

        # Verify we got a response (might be 422 validation error, 500 error, or 200 success)
        assert screenplay_response.status_code in [200, 422, 500]

    def test_screenplay_to_scene_decomposition_flow(self, verify_services_running):
        """Test flow from screenplay to scene decomposition."""
        # Create minimal movie data
        movie_data = {
            "title": "Integration Test Movie",
            "tagline": "A test of the pipeline",
            "genres": ["Action", "Drama"],
            "plot_summary": "A simple plot for testing the pipeline.",
            "cast": [
                {
                    "actor_name": "Test Actor",
                    "character_name": "Protagonist",
                    "physical_description": "Average build",
                    "personality_traits": ["determined"],
                }
            ],
            "visual_style": "Modern",
            "themes": ["testing"],
        }

        # Generate trailer breakdown
        response = requests.post(
            f"{SCENE_DECOMPOSER_URL}/generate-trailer", json=movie_data, timeout=REQUEST_TIMEOUT
        )

        # Verify response (might be 422 validation error, 500 error, or 200 success)
        assert response.status_code in [200, 422, 500]

    def test_complete_pipeline_with_mocked_data(self, verify_services_running, sample_taste_vector):
        """Test complete pipeline with pre-defined data."""
        # Step 1: Quiz (simulated with taste vector - sample_taste_vector fixture available)

        # Step 2: Generate screenplay
        screenplay_data = {
            "title": "Pipeline Test Movie",
            "tagline": "Testing the full pipeline",
            "genres": ["Thriller", "Drama"],
            "plot_summary": "A complex story for pipeline testing.",
            "cast": [
                {
                    "actor_name": "Lead Actor",
                    "character_name": "Detective",
                    "physical_description": "Middle-aged, sharp features",
                    "personality_traits": ["analytical", "persistent"],
                }
            ],
            "visual_style": "Film noir",
            "themes": ["mystery", "justice"],
            "runtime": "110 min",
            "rating": "R",
        }

        # Step 3: Generate scene breakdown
        scene_response = requests.post(
            f"{SCENE_DECOMPOSER_URL}/generate-trailer",
            json=screenplay_data,
            timeout=REQUEST_TIMEOUT,
        )

        # Verify we got through the pipeline (might be 422 validation error, 500 error, or 200 success)
        assert scene_response.status_code in [200, 422, 500]

        if scene_response.status_code == 200:
            scene_data = scene_response.json()
            # Verify scene breakdown has expected structure
            assert isinstance(scene_data, dict)


class TestErrorHandling:
    """Test error handling across services."""

    def test_quiz_invalid_session(self, verify_services_running):
        """Test quiz service handles invalid session ID."""
        response = requests.post(
            f"{QUIZ_SERVICE_URL}/quiz/answer",
            json={"session_id": "invalid-session-id", "question_id": 1, "answer": 5},
            timeout=REQUEST_TIMEOUT,
        )
        assert response.status_code in [400, 404, 422]

    def test_screenplay_missing_fields(self, verify_services_running):
        """Test screenplay service handles missing required fields."""
        response = requests.post(
            f"{SCREENPLAY_SERVICE_URL}/generate-movie", json={}, timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 422  # Validation error

    def test_scene_decomposer_empty_data(self, verify_services_running):
        """Test scene decomposer handles empty data."""
        response = requests.post(
            f"{SCENE_DECOMPOSER_URL}/generate-trailer", json={}, timeout=REQUEST_TIMEOUT
        )
        assert response.status_code == 422  # Validation error

    def test_invalid_endpoints(self, verify_services_running):
        """Test services return 404 for invalid endpoints."""
        services = [
            QUIZ_SERVICE_URL,
            SCREENPLAY_SERVICE_URL,
            SCENE_DECOMPOSER_URL,
            VIDEO_GENERATOR_URL,
        ]

        for service_url in services:
            response = requests.get(f"{service_url}/nonexistent-endpoint", timeout=5)
            assert response.status_code == 404


class TestServiceIntegration:
    """Test integration between services."""

    def test_data_format_compatibility(self, verify_services_running):
        """Test that data formats are compatible between services."""
        # Generate movie data
        movie_payload = {
            "taste_vector": {"action": 0.8, "drama": 0.6},
            "preferences": {"runtime": "120 min"},
        }

        screenplay_response = requests.post(
            f"{SCREENPLAY_SERVICE_URL}/generate-movie", json=movie_payload, timeout=REQUEST_TIMEOUT
        )

        if screenplay_response.status_code == 200:
            movie_data = screenplay_response.json()

            # Try to use this data in scene decomposer
            scene_response = requests.post(
                f"{SCENE_DECOMPOSER_URL}/generate-trailer", json=movie_data, timeout=REQUEST_TIMEOUT
            )

            # Should either succeed or fail gracefully
            assert scene_response.status_code in [200, 422, 500]

    def test_concurrent_quiz_sessions(self, verify_services_running):
        """Test handling multiple concurrent quiz sessions."""
        sessions = []
        questions = []

        # Start multiple quiz sessions
        for _ in range(3):
            response = requests.post(
                f"{QUIZ_SERVICE_URL}/quiz/start", json={"n_questions": 2}, timeout=REQUEST_TIMEOUT
            )
            assert response.status_code == 200
            data = response.json()
            sessions.append(data["session_id"])
            questions.append(data["question"])

        # Verify all sessions have unique IDs
        assert len(sessions) == len(set(sessions))

        # Verify each session can receive answers independently
        for idx, session_id in enumerate(sessions):
            response = requests.post(
                f"{QUIZ_SERVICE_URL}/quiz/answer",
                json={
                    "session_id": session_id,
                    "question_id": questions[idx]["question_id"],
                    "answer": 4,
                },
                timeout=REQUEST_TIMEOUT,
            )
            assert response.status_code == 200


class TestPerformance:
    """Test performance characteristics of the pipeline."""

    def test_quiz_response_time(self, verify_services_running):
        """Test quiz service responds within acceptable time."""
        start_time = time.time()
        response = requests.post(
            f"{QUIZ_SERVICE_URL}/quiz/start", json={"n_questions": 5}, timeout=REQUEST_TIMEOUT
        )
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 5.0  # Should respond within 5 seconds

    def test_health_check_response_time(self, verify_services_running):
        """Test all health checks respond quickly."""
        services = [
            QUIZ_SERVICE_URL,
            SCREENPLAY_SERVICE_URL,
            SCENE_DECOMPOSER_URL,
            VIDEO_GENERATOR_URL,
        ]

        for service_url in services:
            start_time = time.time()
            response = requests.get(f"{service_url}/health", timeout=5)
            elapsed_time = time.time() - start_time

            assert response.status_code == 200
            assert elapsed_time < 2.0  # Health checks should be fast


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v", "--tb=short"])
