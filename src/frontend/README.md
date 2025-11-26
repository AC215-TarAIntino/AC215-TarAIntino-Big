# TarAIntino Frontend

A Next.js React application that provides an interactive quiz interface and orchestrates the AI movie trailer generation pipeline.

## Overview

The frontend serves as the **orchestration layer** for the entire TarAIntino system. It handles:
- User interactions through an interactive movie preference quiz
- Sequential calls to all backend microservices
- Real-time progress tracking during video generation
- Video playback and result display

## Technology Stack

- **Framework**: Next.js 15.5 with React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **Animations**: Framer Motion, GSAP, React Spring
- **UI Components**: Radix UI, Lucide Icons
- **Port**: 3002 (development), 3000 (production in Docker)

## Project Structure

```
frontend/
├── app/
│   ├── api/                    # API Routes (orchestration)
│   │   ├── generate-video/     # Trigger trailer generation
│   │   └── video-status/       # Check generation status
│   ├── generating/             # Loading/progress page
│   ├── result/                 # Video playback page
│   ├── page.tsx                # Home page with quiz
│   └── layout.tsx              # Root layout
├── components/                 # Reusable React components
├── lib/                        # Utilities and helpers
└── public/                     # Static assets
```

## How It Works

### 1. Quiz Phase
- User lands on the home page (`app/page.tsx`)
- Interactive quiz presents movie preference questions
- Frontend calls Quiz Service API endpoints:
  - `POST http://localhost:8082/quiz/start`
  - `POST http://localhost:8082/quiz/answer`
  - `POST http://localhost:8082/recommend`

### 2. Trailer Generation (Orchestration)
When the user clicks "Generate Trailer", the frontend orchestrates the full pipeline through its API routes (`app/api/generate-video/`):

**Sequential calls to backend services:**
```
1. Screenplay Writer    → POST http://localhost:8080/generate-movie
2. Scene Decomposer     → POST http://localhost:8001/generate-trailer
3. Video Generator      → POST http://localhost:8003/generate/trailer
```

Each service's output becomes the input for the next service.

### 3. Progress Tracking
- User is redirected to `/generating` page
- Frontend polls `app/api/video-status/` endpoint
- Status checks GCS bucket for completed video
- Real-time progress animations keep user engaged

### 4. Video Playback
- Once complete, user redirected to `/result` page
- Video is streamed from GCS bucket (`tarantaino-output`)
- User can download or regenerate trailer

## Running Locally

-> See main [README](../README.md) for full setup instructions.

## Environment Variables

The frontend uses the following environment variables (optional in development):

```bash
NEXT_PUBLIC_QUIZ_API_URL=http://localhost:8082
NEXT_PUBLIC_API_BASE_URL=http://localhost:3000/api
```

## API Routes

### `POST /api/generate-video`
Orchestrates the full trailer generation pipeline.

**Request Body:**
```json
{
  "sessionId": "quiz-session-id",
  "recommendations": [
    {"title": "Movie Title", "score": 0.95}
  ]
}
```

**Response:**
```json
{
  "status": "processing",
  "jobId": "unique-job-id"
}
```

### `GET /api/video-status?jobId={id}`
Checks the status of video generation.

**Response:**
```json
{
  "status": "complete",
  "videoUrl": "https://storage.googleapis.com/tarantaino-output/..."
}
```

## Key Features

- **Interactive Quiz**: Smooth animations and transitions for engaging UX
- **Real-time Progress**: Live updates during 2-5 minute video generation
- **Responsive Design**: Works on desktop and mobile
- **Error Handling**: Graceful fallbacks if backend services fail
- **Confetti Celebration**: Fun animation when trailer is ready 🎉

## Notes

- The frontend **does not persist state** - all session data is managed in backend services
- Video URLs are temporary and expire after 24 hours (GCS signed URLs)
- API routes handle CORS for backend service communication
- The orchestration logic in API routes can be extended with retry logic, timeouts, and better error handling

## Related Documentation

- [Main Project README](../README.md)
- [System Architecture](../hand-ins/system-architecture-diagram.md)
- [Quiz Service](../quiz-vector/README.md)
