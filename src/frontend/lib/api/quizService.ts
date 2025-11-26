import type {
  StartQuizRequest,
  StartQuizResponse,
  SubmitAnswerRequest,
  AnswerResponse,
  CompleteQuizRequest,
  CompleteResponse,
  RecommendRequest,
  RecommendResponse,
  HealthResponse,
} from "./types";

const QUIZ_API_URL =
  process.env.NEXT_PUBLIC_QUIZ_API_URL || "http://localhost:8082";

class QuizApiError extends Error {
  constructor(
    message: string,
    public status?: number
  ) {
    super(message);
    this.name = "QuizApiError";
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${QUIZ_API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new QuizApiError(
      `API error: ${response.status} - ${errorText}`,
      response.status
    );
  }

  return response.json();
}

export async function checkHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>("/health");
}

export async function startQuiz(
  numQuestions: number = 5,
  ttlSeconds: number = 1800
): Promise<StartQuizResponse> {
  const request: StartQuizRequest = {
    num_questions: numQuestions,
    ttl_seconds: ttlSeconds,
  };

  return fetchApi<StartQuizResponse>("/quiz/start", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function submitAnswer(
  sessionId: string,
  questionId: number,
  answer: number
): Promise<AnswerResponse> {
  const request: SubmitAnswerRequest = {
    session_id: sessionId,
    question_id: questionId,
    answer,
  };

  return fetchApi<AnswerResponse>("/quiz/answer", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function completeQuiz(
  sessionId: string
): Promise<CompleteResponse> {
  const request: CompleteQuizRequest = {
    session_id: sessionId,
  };

  return fetchApi<CompleteResponse>("/quiz/complete", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getRecommendations(
  sessionId: string,
  topN: number = 10
): Promise<RecommendResponse> {
  const request: RecommendRequest = {
    session_id: sessionId,
    top_n: topN,
  };

  return fetchApi<RecommendResponse>("/recommend", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export { QuizApiError };
