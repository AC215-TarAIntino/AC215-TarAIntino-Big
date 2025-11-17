from pydantic import BaseModel, Field
from typing import Optional, List

class StartRequest(BaseModel):
    num_questions: int = Field(5, ge=1, le=16)  # you can ignore on server if you like
    ttl_seconds: int = Field(1800, ge=60, le=86400)

class Question(BaseModel):
    question_id: int
    tag_id: int
    tag_label: str
    scale: dict

class StartResponse(BaseModel):
    session_id: str
    question: Question

class AnswerRequest(BaseModel):
    session_id: str
    question_id: int
    answer: float  # 1..10

class AnswerResponse(BaseModel):
    status: str                 # "ok" | "complete"
    next_question: Optional[Question] = None
    progress: dict              # {"asked": x, "total": K}

class CompleteRequest(BaseModel):
    session_id: str

class CompleteResponse(BaseModel):
    taste_vector: List[float]   # length D
    dims: int
    progress: dict

class RecommendRequest(BaseModel):
    session_id: str
    top_n: int = 10
class RecommendResponse(BaseModel):
    results: list