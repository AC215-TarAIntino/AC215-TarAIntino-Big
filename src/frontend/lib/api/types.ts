// Request types
export interface StartQuizRequest {
  num_questions: number;
  ttl_seconds?: number;
}

export interface SubmitAnswerRequest {
  session_id: string;
  question_id: number;
  answer: number;
}

export interface CompleteQuizRequest {
  session_id: string;
}

export interface RecommendRequest {
  session_id: string;
  top_n: number;
}

// Response types
export interface Question {
  question_id: number;
  tag_id: number;
  tag_label: string;
  scale: {
    min: number;
    max: number;
  };
}

export interface StartQuizResponse {
  session_id: string;
  question: Question;
}

export interface Progress {
  asked: number;
  total: number;
}

export interface AnswerResponse {
  status: "ok" | "complete";
  next_question: Question | null;
  progress: Progress;
}

export interface CompleteResponse {
  taste_vector: number[];
  dims: number;
  progress: Progress;
}

export interface MovieRecommendation {
  movie_id: string;
  title: string;
  score: number;
}

export interface RecommendResponse {
  results: MovieRecommendation[];
}

export interface HealthResponse {
  ok: boolean;
}

// Frontend state types
export interface QuizState {
  sessionId: string | null;
  currentQuestion: Question | null;
  progress: Progress;
  isLoading: boolean;
  error: string | null;
}
