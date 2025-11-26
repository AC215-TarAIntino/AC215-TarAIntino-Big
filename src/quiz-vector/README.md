# Quiz Vector Service

A FastAPI service that provides an interactive movie preference quiz and generates personalized movie recommendations using Bayesian inference and vector similarity search.

## Overview

The Quiz Vector service handles two key responsibilities:
1. **Interactive Quiz**: Collect user movie preferences through an adaptive questionnaire
2. **RAG (Retrieval-Augmented Generation)**: Generate movie recommendations using ChromaDB vector similarity search

## Technology Stack

- **Framework**: FastAPI (Python)
- **Database**: ChromaDB (vector database)
- **Machine Learning**: NumPy, scikit-learn, SciPy
- **Cloud Storage**: Google Cloud Storage (GCS)
- **Data Processing**: Pandas, tqdm
- **Port**: 8082

## Project Structure

```
quiz-vector/
├── src/
│   ├── datapipeline/           # Data ingestion module
│   │   ├── downloader.py       # GCS → ChromaDB loader
│   │   ├── uploader.py         # Upload datasets to GCS
│   │   └── logs/               # Cached prior statistics
│   └── quiz_service/           # Quiz API module
│       ├── api.py              # FastAPI endpoints
│       ├── model.py            # Bayesian taste model
│       ├── config.py           # ChromaDB connection
│       ├── state.py            # Session management
│       ├── schemas.py          # Request/response models
│       └── utils.py            # Similarity search utilities
├── secrets/                    # GCS credentials
├── docker-compose.yml          # Local orchestration
├── Dockerfile                  # Container definition
└── pyproject.toml              # Python dependencies
```

## How It Works

### 1. Data Pipeline (`src/datapipeline/`)

**Purpose**: Load movie-tag relevance data from GCS into ChromaDB

**Dataset**:
- **Source**: MovieLens Tag Genome Dataset (2014)
- **Size**: 11 million tag-movie relevance scores
- **Movies**: 9,734 movies
- **Tags**: 1,128 unique tags
- **Storage**: GCS bucket `tag-genome-data`

**Process**:
```
GCS (tag_relevance.dat)
  → downloader.py
    → Parse & vectorize
      → ChromaDB (movie_tag_relevance_cos collection)
        → Cache prior mean/covariance
```

The `chroma-init` service automatically runs this on startup.

### 2. Quiz Service (`src/quiz_service/`)

**Purpose**: Generate personalized movie recommendations based on user preferences

**How the quiz works**:
1. **Start Session**: User starts quiz → Creates unique session with initial taste vector
2. **Ask Questions**: Service selects informative tags to ask about (e.g., "Rate 'sci-fi' 1-10")
3. **Update Beliefs**: Each answer updates the taste vector using **Bayesian inference**
4. **Iterate**: Repeat for 5-10 questions to refine user preferences
5. **Recommend**: Perform **cosine similarity search** in ChromaDB to find matching movies

**Bayesian Taste Model** (`model.py`):
- Maintains a **1,128-dimensional taste vector** (one per tag)
- Uses **Gaussian distribution** with mean and covariance
- Updates beliefs with each user rating using Bayesian inference
- Uncertainty decreases with each question answered

### 3. API Endpoints

#### `POST /quiz/start`
Start a new quiz session.

**Request:**
```json
{
  "num_questions": 5
}
```

**Response:**
```json
{
  "session_id": "abc123",
  "question": {
    "question_id": 1,
    "tag_label": "sci-fi",
    "tag_description": "Science fiction themes"
  }
}
```

#### `POST /quiz/answer`
Submit an answer and get the next question.

**Request:**
```json
{
  "session_id": "abc123",
  "question_id": 1,
  "answer": 8
}
```

**Response:**
```json
{
  "status": "in_progress",
  "next_question": {
    "question_id": 2,
    "tag_label": "action",
    "tag_description": "Action-packed scenes"
  }
}
```

#### `POST /recommend`
Get movie recommendations based on completed quiz.

**Request:**
```json
{
  "session_id": "abc123",
  "top_n": 10
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "title": "Blade Runner",
      "score": 0.95,
      "genres": ["Sci-Fi", "Thriller"]
    }
  ]
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Running Locally

-> See main [README](../README.md) for full setup instructions.

## Environment Variables

The Quiz Service requires these environment variables:

```bash
# ChromaDB Connection
CHROMA_SERVER_HOST=chroma
CHROMA_SERVER_PORT=8000
CHROMA_COLLECTION=movie_tag_relevance_cos

# GCS Credentials
GOOGLE_APPLICATION_CREDENTIALS=/app/adc.json

# Cached Prior Statistics
PRIOR_MEAN_PATH=/app/src/datapipeline/logs/prior_mean.npy
PRIOR_COV_PATH=/app/src/datapipeline/logs/prior_cov.npy
TAG_INDEX_JSON=/app/src/datapipeline/logs/movie_tag_relevance_cos__tag_index.json
```

## Key Features

- **Adaptive Questioning**: Intelligently selects which tags to ask about based on information gain
- **Bayesian Inference**: Statistically sound preference modeling with uncertainty quantification
- **Fast Vector Search**: ChromaDB enables sub-second similarity search across 10k movies
- **Session Management**: Maintains state for multiple concurrent users
- **Cached Statistics**: Pre-computed prior mean/covariance for fast initialization

## Data Flow

```
User → Frontend → Quiz Service API
                      ↓
                  Session State
                      ↓
                 Taste Vector (Bayesian Update)
                      ↓
                  ChromaDB Vector Search
                      ↓
              Top-N Movie Recommendations
                      ↓
               Frontend → User
```

## Notes

- **Session Expiry**: Sessions timeout after 30 minutes of inactivity
- **Scalability**: In-memory session storage (use Redis for production)
- **Cold Start**: First request may be slow due to ChromaDB initialization
- **Data Source**: MovieLens Tag Genome Dataset is static (no real-time updates)

## Related Documentation

- [Main Project README](../README.md)
- [System Architecture](../hand-ins/system-architecture-diagram.md)
- [Frontend Documentation](../frontend/README.md)
