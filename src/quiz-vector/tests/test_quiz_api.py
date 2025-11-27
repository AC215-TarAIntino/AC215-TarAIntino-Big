import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from fastapi.testclient import TestClient
from src.quiz_service.api import app, _new_session_model


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_dependencies():
    with patch("src.quiz_service.api.get_prior_mean") as mock_mean, \
         patch("src.quiz_service.api.get_prior_cov") as mock_cov, \
         patch("src.quiz_service.api.get_tagid2col") as mock_tagid2col, \
         patch("src.quiz_service.api.STORE") as mock_store, \
         patch("src.quiz_service.api.get_collection") as mock_collection:

        mock_mean.return_value = np.zeros(100)
        mock_cov.return_value = np.eye(100)
        mock_tagid2col.return_value = {i: i for i in range(100)}

        yield {
            "mean": mock_mean,
            "cov": mock_cov,
            "tagid2col": mock_tagid2col,
            "store": mock_store,
            "collection": mock_collection
        }


class TestNewSessionModel:
    @patch("src.quiz_service.api.get_prior_mean")
    @patch("src.quiz_service.api.get_prior_cov")
    @patch("src.quiz_service.api.get_tagid2col")
    @patch("src.quiz_service.api.QUIZ_TAGS", [(i, f"tag{i}") for i in range(16)])
    def test_new_session_model_creation(self, mock_tagid2col, mock_cov, mock_mean):
        mock_mean.return_value = np.zeros(100)
        mock_cov.return_value = np.eye(100)
        mock_tagid2col.return_value = {i: i for i in range(100)}

        model = _new_session_model(10)

        assert model is not None
        assert model.target == 10

    @patch("src.quiz_service.api.get_prior_mean")
    @patch("src.quiz_service.api.get_prior_cov")
    @patch("src.quiz_service.api.get_tagid2col")
    @patch("src.quiz_service.api.QUIZ_TAGS", [(i, f"tag{i}") for i in range(16)])
    def test_new_session_model_clamps_target(self, mock_tagid2col, mock_cov, mock_mean):
        mock_mean.return_value = np.zeros(100)
        mock_cov.return_value = np.eye(100)
        mock_tagid2col.return_value = {i: i for i in range(100)}

        model = _new_session_model(100)

        assert model.target == 16


class TestHealthEndpoint:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


class TestQuizStart:
    @patch("src.quiz_service.api._new_session_model")
    @patch("src.quiz_service.api.STORE")
    def test_quiz_start_success(self, mock_store, mock_new_model, client):
        mock_model = Mock()
        mock_model.pick_next_quiz_tag.return_value = 0
        mock_model.current_question_payload.return_value = {
            "question_id": 0,
            "tag_id": 416,
            "tag_label": "funny",
            "scale": {"min": 1, "max": 10}
        }
        mock_new_model.return_value = mock_model
        mock_store.create.return_value = "session-123"

        response = client.post("/quiz/start", json={"num_questions": 5, "ttl_seconds": 3600})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "question" in data
        assert data["session_id"] == "session-123"

    @patch("src.quiz_service.api._new_session_model")
    @patch("src.quiz_service.api.STORE")
    def test_quiz_start_with_default_ttl(self, mock_store, mock_new_model, client):
        mock_model = Mock()
        mock_model.pick_next_quiz_tag.return_value = 0
        mock_model.current_question_payload.return_value = {
            "question_id": 0,
            "tag_id": 416,
            "tag_label": "funny",
            "scale": {"min": 1, "max": 10}
        }
        mock_new_model.return_value = mock_model
        mock_store.create.return_value = "session-123"

        response = client.post("/quiz/start", json={"num_questions": 5})

        assert response.status_code == 200


class TestQuizAnswer:
    @patch("src.quiz_service.api.STORE")
    def test_quiz_answer_success(self, mock_store, client):
        mock_model = Mock()
        mock_model.K = 100
        mock_model.target = 5
        mock_model.quiz_status.return_value = {"asked": 1, "remaining": 4}
        mock_model.pick_next_quiz_tag.return_value = 1
        mock_model.current_question_payload.return_value = {
            "question_id": 1,
            "tag_id": 284,
            "tag_label": "dark",
            "scale": {"min": 1, "max": 10}
        }

        mock_session = Mock()
        mock_session.model = mock_model
        mock_store.get.return_value = mock_session

        response = client.post("/quiz/answer", json={
            "session_id": "session-123",
            "question_id": "0",
            "answer": 5
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "next_question" in data
        assert "progress" in data

    @patch("src.quiz_service.api.STORE")
    def test_quiz_answer_session_not_found(self, mock_store, client):
        mock_store.get.return_value = None

        response = client.post("/quiz/answer", json={
            "session_id": "invalid-session",
            "question_id": "0",
            "answer": 5
        })

        assert response.status_code == 404

    @patch("src.quiz_service.api.STORE")
    def test_quiz_answer_invalid_question_id(self, mock_store, client):
        mock_model = Mock()
        mock_model.K = 10
        mock_session = Mock()
        mock_session.model = mock_model
        mock_store.get.return_value = mock_session

        response = client.post("/quiz/answer", json={
            "session_id": "session-123",
            "question_id": "100",
            "answer": 5
        })

        assert response.status_code == 400

    @patch("src.quiz_service.api.STORE")
    def test_quiz_answer_complete(self, mock_store, client):
        mock_model = Mock()
        mock_model.K = 100
        mock_model.target = 5
        mock_model.quiz_status.return_value = {"asked": 5, "remaining": 0}

        mock_session = Mock()
        mock_session.model = mock_model
        mock_store.get.return_value = mock_session

        response = client.post("/quiz/answer", json={
            "session_id": "session-123",
            "question_id": "4",
            "answer": 5
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["next_question"] is None


class TestQuizComplete:
    @patch("src.quiz_service.api.STORE")
    def test_quiz_complete_success(self, mock_store, client):
        mock_model = Mock()
        mock_model.export_taste_vector.return_value = np.array([1.0, 2.0, 3.0])
        mock_model.quiz_status.return_value = {"asked": 5, "remaining": 0}

        mock_session = Mock()
        mock_session.model = mock_model
        mock_store.get.return_value = mock_session

        response = client.post("/quiz/complete", json={"session_id": "session-123"})

        assert response.status_code == 200
        data = response.json()
        assert "taste_vector" in data
        assert "dims" in data
        assert "progress" in data
        assert data["dims"] == 3
        assert len(data["taste_vector"]) == 3

    @patch("src.quiz_service.api.STORE")
    def test_quiz_complete_session_not_found(self, mock_store, client):
        mock_store.get.return_value = None

        response = client.post("/quiz/complete", json={"session_id": "invalid-session"})

        assert response.status_code == 404


class TestRecommend:
    @patch("src.quiz_service.api.STORE")
    @patch("src.quiz_service.api.get_collection")
    @patch("src.quiz_service.api.topN_from_matrix")
    def test_recommend_success(self, mock_topn, mock_collection, mock_store, client):
        mock_model = Mock()
        mock_model.export_taste_vector.return_value = np.array([1.0, 2.0, 3.0])

        mock_session = Mock()
        mock_session.model = mock_model
        mock_store.get.return_value = mock_session

        mock_col = Mock()
        mock_col.get.return_value = {
            "ids": ["1", "2", "3"],
            "embeddings": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
            "metadatas": [{"movieId": 1, "title": "Movie 1"},
                         {"movieId": 2, "title": "Movie 2"},
                         {"movieId": 3, "title": "Movie 3"}]
        }
        mock_collection.return_value = mock_col

        mock_topn.return_value = [
            {"movie_id": "1", "title": "Movie 1", "score": 0.9},
            {"movie_id": "2", "title": "Movie 2", "score": 0.8}
        ]

        response = client.post("/recommend", json={
            "session_id": "session-123",
            "top_n": 2
        })

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2

    @patch("src.quiz_service.api.STORE")
    def test_recommend_session_not_found(self, mock_store, client):
        mock_store.get.return_value = None

        response = client.post("/recommend", json={
            "session_id": "invalid-session",
            "top_n": 10
        })

        assert response.status_code == 404

    @patch("src.quiz_service.api.STORE")
    @patch("src.quiz_service.api.get_collection")
    def test_recommend_no_embeddings(self, mock_collection, mock_store, client):
        mock_model = Mock()
        mock_model.export_taste_vector.return_value = np.array([1.0, 2.0, 3.0])

        mock_session = Mock()
        mock_session.model = mock_model
        mock_store.get.return_value = mock_session

        mock_col = Mock()
        mock_col.get.return_value = {
            "ids": [],
            "embeddings": [],
            "metadatas": []
        }
        mock_collection.return_value = mock_col

        response = client.post("/recommend", json={
            "session_id": "session-123",
            "top_n": 10
        })

        assert response.status_code == 503


class TestStartupEvent:
    @patch("src.quiz_service.api._compute_and_save_prior_if_needed")
    @patch("src.quiz_service.api.get_tagid2col")
    @patch("src.quiz_service.api.get_prior_mean")
    @patch("src.quiz_service.api.get_prior_cov")
    def test_startup_calls_required_functions(self, mock_cov, mock_mean, mock_tagid2col, mock_compute):
        from src.quiz_service.api import _startup

        _startup()

        mock_compute.assert_called_once()
        mock_tagid2col.assert_called_once()
        mock_mean.assert_called_once()
        mock_cov.assert_called_once()