import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    QUIZ_TAGS,
    get_collection,
    get_prior_cov,
    get_prior_mean,
    get_tagid2col,
)
from .model import FullCovarianceTasteModel
from .schemas import (
    AnswerRequest,
    AnswerResponse,
    CompleteRequest,
    CompleteResponse,
    Question,
    RecommendRequest,
    RecommendResponse,
    StartRequest,
    StartResponse,
)
from .state import STORE
from .utils import _compute_and_save_prior_if_needed, topN_from_matrix

app = FastAPI(title="Quiz-Vector Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _new_session_model(target_questions: int):
    prior_mean = get_prior_mean().copy()
    prior_cov = get_prior_cov().copy()
    tagid2col = get_tagid2col()
    # clamp target to the number of quiz tags
    target = max(1, min(target_questions, len(QUIZ_TAGS)))
    return FullCovarianceTasteModel(
        prior_mean=prior_mean,
        prior_cov=prior_cov,
        tagid2col=tagid2col,
        quiz_tags=QUIZ_TAGS,
        sigma2=0.05,
        target_questions=target,
    )


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/quiz/start", response_model=StartResponse)
def quiz_start(req: StartRequest):
    model = _new_session_model(req.num_questions)
    sid = STORE.create(model, ttl_sec=req.ttl_seconds)
    k = model.pick_next_quiz_tag()
    q = Question(**model.current_question_payload(k))
    return StartResponse(session_id=sid, question=q)


@app.post("/quiz/answer", response_model=AnswerResponse)
def quiz_answer(req: AnswerRequest):
    s = STORE.get(req.session_id)
    if not s:
        raise HTTPException(404, "session not found or expired")

    m = s.model
    k = int(req.question_id)
    if k < 0 or k >= m.K:
        raise HTTPException(400, "invalid question_id")

    m.update_with_answer(k, req.answer)
    progress = m.quiz_status()

    # stop if we’ve asked as many as target
    if progress["asked"] >= m.target:
        return AnswerResponse(status="complete", next_question=None, progress=progress)

    k_next = m.pick_next_quiz_tag()
    q = Question(**m.current_question_payload(k_next))
    return AnswerResponse(status="ok", next_question=q, progress=progress)


@app.post("/quiz/complete", response_model=CompleteResponse)
def quiz_complete(req: CompleteRequest):
    s = STORE.get(req.session_id)
    if not s:
        raise HTTPException(404, "session not found or expired")
    m = s.model
    tv = m.export_taste_vector().tolist()
    return CompleteResponse(taste_vector=tv, dims=len(tv), progress=m.quiz_status())


@app.on_event("startup")
def _startup():
    _compute_and_save_prior_if_needed()
    _ = get_tagid2col()
    _ = get_prior_mean()
    _ = get_prior_cov()


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    s = STORE.get(req.session_id)
    if not s:
        raise HTTPException(404, "session not found or expired")

    col = get_collection()

    sample = col.get(
        limit=max(1, min(500, req.top_n * 50)),
        include=["embeddings", "metadatas"],  # keep ids out of include
    )

    ids = sample.get("ids")
    if ids is None:
        ids = []

    embs = sample.get("embeddings")
    if embs is None:
        embs = []

    metas = sample.get("metadatas")
    if metas is None:
        metas = []

    # Prefer Chroma-provided ids if present; otherwise derive from metadata/movieId
    ids = sample.get("ids")
    if not ids:
        ids = [str(m.get("movieId", i)) for i, m in enumerate(metas)]

    if len(ids) == 0 or len(embs) == 0:
        raise HTTPException(503, "No candidate embeddings available in Chroma.")

    # Build a strict 2D float64 matrix; handle ragged cases
    try:
        X = np.asarray(embs, dtype=np.float64)
        if X.ndim != 2:
            X = np.vstack([np.asarray(e, dtype=np.float64) for e in embs])
    except Exception:
        X = np.vstack([np.asarray(e, dtype=np.float64) for e in embs])

    m = min(len(ids), X.shape[0])
    ids, metas, X = ids[:m], (metas or [{}] * m)[:m], X[:m, :]

    theta = s.model.export_taste_vector()
    results = topN_from_matrix(theta, X, ids, metas, N=req.top_n)
    return RecommendResponse(results=results)
