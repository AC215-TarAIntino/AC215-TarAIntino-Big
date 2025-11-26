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
    User -->|Take Movie Preference Quiz| FE
    FE -->|POST /quiz/start<br/>POST /quiz/answer| QS
    QS -->|POST /recommend<br/>Movie Recommendations| FE

    %% Frontend Orchestrates Pipeline
    FE -->|a. Screenplay<br/>POST /generate-movie| SW
    FE -->|b. Scenes<br/>POST /generate-trailer| SD
    FE -->|c. Video<br/>POST /generate/trailer| VG

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
    GCS_OUT -->|Show Final Trailer| FE
    FE -->|Watch Final Trailer| User

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

# System Architecture Overview
Frontend API routes handle sequential calls to backend services:
1. **Quiz Phase**: User answers questions → Quiz Service builds taste vector
2. **Recommendations**: Frontend gets movie recommendations from Quiz Service
3. **Screenplay Generation**: Frontend calls Screenplay Writer with recommendations
4. **Scene Breakdown**: Frontend sends screenplay to Scene Decomposer
5. **Video Generation**: Frontend triggers Video Generator with scene breakdown
6. **Delivery**: Frontend polls GCS and streams completed video to user