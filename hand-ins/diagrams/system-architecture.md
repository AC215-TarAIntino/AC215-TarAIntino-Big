# System Architecture Diagram

```mermaid
graph TB
    %% Define all nodes
    User([👤 User])
    FE[🎨 Frontend<br/>Next.js + API Routes<br/>Port: 3000<br/><i>Orchestrates Pipeline</i>]

    QS[📊 Quiz Service<br/>FastAPI<br/>Port: 8082]
    SW[✍️ Screenplay Writer<br/>FastAPI<br/>Port: 8080]
    SD[🎞️ Scene Decomposer<br/>FastAPI<br/>Port: 8001]
    VG[🎥 Video Generator<br/>FastAPI<br/>Port: 8003]

    CHROMA[(🗄️ ChromaDB<br/>Vector Database<br/>Port: 8000)]
    INIT[⚙️ chroma-init<br/>Data Loader]

    GCS_DATA[(☁️ GCS<br/>tag-genome-data<br/>Dataset)]
    GCS_OUT[(☁️ GCS<br/>tarantaino-output<br/>Videos)]

    OMDB[🎬 OMDb API<br/>Movie Metadata]
    OR[🤖 OpenRouter<br/>LLM Provider<br/>Gemini/Claude]
    GEMINI[✨ Google Gemini<br/>Imagen 3<br/>VEO 3.1]

    %% User Flow - Quiz Phase
    User -->|1. Takes Quiz| FE
    FE -->|POST /quiz/start<br/>POST /quiz/answer| QS
    QS -->|POST /recommend<br/>Movie Recommendations| FE

    %% Frontend Orchestrates Pipeline
    FE -->|2. Generate Screenplay<br/>POST /generate-movie| SW
    FE -->|3. Generate Scenes<br/>POST /generate-trailer| SD
    FE -->|4. Generate Video<br/>POST /generate/trailer| VG

    %% Quiz Service Data Flow
    CHROMA -->|Vector Similarity<br/>Search| QS
    GCS_DATA -->|Download<br/>Dataset| INIT
    INIT -->|Populate<br/>Embeddings| CHROMA

    %% Screenplay Writer Dependencies
    SW -->|GET movie<br/>metadata| OMDB
    SW -->|Generate<br/>screenplay| OR

    %% Scene Decomposer Dependencies
    SD -->|Generate scene<br/>breakdown| OR

    %% Video Generator Dependencies
    VG -->|Generate character<br/>references| GEMINI
    VG -->|Generate scene<br/>videos| GEMINI
    VG -->|Upload final<br/>trailer| GCS_OUT

    %% Final Delivery
    GCS_OUT -->|5. Stream Video| FE
    FE -->|Deliver| User

    %% Styling
    classDef frontend fill:#e1f5ff,stroke:#0066cc,stroke-width:4px
    classDef microservice fill:#fff4e1,stroke:#ff9800,stroke-width:2px
    classDef database fill:#f0e1ff,stroke:#9c27b0,stroke-width:2px
    classDef storage fill:#e1ffe1,stroke:#4caf50,stroke-width:2px
    classDef external fill:#ffe1e1,stroke:#f44336,stroke-width:2px
    classDef user fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px

    class User user
    class FE frontend
    class QS,SW,SD,VG microservice
    class CHROMA,INIT database
    class GCS_DATA,GCS_OUT storage
    class OMDB,OR,GEMINI external
```

## Key Changes from Previous Architecture

**Pipeline Orchestration Now Handled by Frontend:**
- The `pipeline2.py` orchestrator has been removed
- Frontend (Next.js) now directly orchestrates the microservices pipeline
- Frontend API routes handle the sequential calls to backend services

## Pipeline Flow

1. **Quiz Phase**: User answers questions → Frontend calls Quiz Service
2. **Recommendations**: Frontend requests recommendations from Quiz Service
3. **Screenplay Generation**: Frontend calls Screenplay Writer with recommendations
4. **Scene Breakdown**: Frontend sends screenplay to Scene Decomposer
5. **Video Generation**: Frontend triggers Video Generator with scene breakdown
6. **Delivery**: Frontend polls GCS for completed video and streams to user

## Advantages of Frontend Orchestration

- **Simplified Architecture**: One less service to deploy and maintain
- **Better User Experience**: Frontend can show real-time progress updates
- **Easier Debugging**: All orchestration logic visible in one place
- **Reduced Latency**: No intermediate service hop
- **State Management**: Frontend naturally manages user session state

## Frontend API Routes Structure

```
frontend/app/api/
├── quiz/
│   ├── start/route.ts          # Proxy to Quiz Service
│   ├── answer/route.ts         # Proxy to Quiz Service
│   └── recommend/route.ts      # Proxy to Quiz Service
└── generate/
    └── route.ts                # Orchestrates full pipeline:
                                # 1. Call Screenplay Writer
                                # 2. Call Scene Decomposer
                                # 3. Call Video Generator
                                # 4. Return GCS URL
```
