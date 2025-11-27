import pytest
from pydantic import ValidationError
from quiz_service.schemas import (
    StartRequest, StartResponse, Question,
    AnswerRequest, AnswerResponse,
    CompleteRequest, CompleteResponse,
    RecommendRequest, RecommendResponse
)


class TestQuestion:
    def test_question_creation(self):
        q = Question(
            question_id=0,
            tag_id=416,
            tag_label="funny",
            scale={"min": 1, "max": 10}
        )
        assert q.question_id == 0
        assert q.tag_id == 416
        assert q.tag_label == "funny"
        assert q.scale == {"min": 1, "max": 10}

    def test_question_dict(self):
        q = Question(
            question_id=1,
            tag_id=284,
            tag_label="dark",
            scale={"min": 1, "max": 10}
        )
        d = q.model_dump()
        assert d["question_id"] == 1
        assert d["tag_id"] == 284


class TestStartRequest:
    def test_start_request_defaults(self):
        req = StartRequest()
        assert req.num_questions == 5
        assert req.ttl_seconds == 1800

    def test_start_request_custom_values(self):
        req = StartRequest(num_questions=10, ttl_seconds=3600)
        assert req.num_questions == 10
        assert req.ttl_seconds == 3600

    def test_start_request_validation_min(self):
        with pytest.raises(ValidationError):
            StartRequest(num_questions=0)

    def test_start_request_validation_max(self):
        with pytest.raises(ValidationError):
            StartRequest(num_questions=17)

    def test_start_request_ttl_validation(self):
        with pytest.raises(ValidationError):
            StartRequest(ttl_seconds=30)  # less than 60
        with pytest.raises(ValidationError):
            StartRequest(ttl_seconds=90000)  # more than 86400


class TestStartResponse:
    def test_start_response_creation(self):
        q = Question(
            question_id=0,
            tag_id=416,
            tag_label="funny",
            scale={"min": 1, "max": 10}
        )
        resp = StartResponse(session_id="test-session-123", question=q)
        assert resp.session_id == "test-session-123"
        assert resp.question.question_id == 0
        assert resp.question.tag_label == "funny"


class TestAnswerRequest:
    def test_answer_request_creation(self):
        req = AnswerRequest(
            session_id="test-session",
            question_id=0,
            answer=7.5
        )
        assert req.session_id == "test-session"
        assert req.question_id == 0
        assert req.answer == 7.5

    def test_answer_request_boundary_values(self):
        req1 = AnswerRequest(session_id="test", question_id=0, answer=1.0)
        assert req1.answer == 1.0

        req2 = AnswerRequest(session_id="test", question_id=0, answer=10.0)
        assert req2.answer == 10.0


class TestAnswerResponse:
    def test_answer_response_ok_status(self):
        q = Question(
            question_id=1,
            tag_id=284,
            tag_label="dark",
            scale={"min": 1, "max": 10}
        )
        resp = AnswerResponse(
            status="ok",
            next_question=q,
            progress={"asked": 1, "total": 5}
        )
        assert resp.status == "ok"
        assert resp.next_question is not None
        assert resp.next_question.question_id == 1
        assert resp.progress["asked"] == 1
        assert resp.progress["total"] == 5

    def test_answer_response_complete_status(self):
        resp = AnswerResponse(
            status="complete",
            next_question=None,
            progress={"asked": 5, "total": 5}
        )
        assert resp.status == "complete"
        assert resp.next_question is None
        assert resp.progress["asked"] == 5


class TestCompleteRequest:
    def test_complete_request_creation(self):
        req = CompleteRequest(session_id="test-session-456")
        assert req.session_id == "test-session-456"


class TestCompleteResponse:
    def test_complete_response_creation(self):
        taste_vec = [0.1, 0.2, 0.3, 0.4, 0.5]
        resp = CompleteResponse(
            taste_vector=taste_vec,
            dims=5,
            progress={"asked": 5, "total": 5}
        )
        assert resp.taste_vector == taste_vec
        assert resp.dims == 5
        assert resp.progress["asked"] == 5

    def test_complete_response_empty_vector(self):
        resp = CompleteResponse(
            taste_vector=[],
            dims=0,
            progress={"asked": 0, "total": 0}
        )
        assert len(resp.taste_vector) == 0
        assert resp.dims == 0


class TestRecommendRequest:
    def test_recommend_request_defaults(self):
        req = RecommendRequest(session_id="test-session")
        assert req.session_id == "test-session"
        assert req.top_n == 10

    def test_recommend_request_custom_top_n(self):
        req = RecommendRequest(session_id="test-session", top_n=20)
        assert req.top_n == 20


class TestRecommendResponse:
    def test_recommend_response_creation(self):
        results = [
            {"movie_id": "1", "title": "Movie 1", "score": 0.95},
            {"movie_id": "2", "title": "Movie 2", "score": 0.89}
        ]
        resp = RecommendResponse(results=results)
        assert len(resp.results) == 2
        assert resp.results[0]["movie_id"] == "1"
        assert resp.results[1]["score"] == 0.89

    def test_recommend_response_empty_results(self):
        resp = RecommendResponse(results=[])
        assert len(resp.results) == 0
