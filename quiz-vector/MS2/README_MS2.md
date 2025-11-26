**Team Members**
Mathilde Cros, Robert Debbas, Maddy Jin, Karlo Vrancic

**Group Name**
TarAIntino

**Project**
In this project, we aim to develop an avant-garde end-to-end AI movie trailer generation application. The app will feature an adaptive, Akinator-style quiz to elicit user preferences and include a modular pipeline connecting those preferences to generative APIs. Users can simply answer a short interactive quiz, and the app will produce a personalized, AI-generated movie trailer that reflects their cinematic taste. Additionally, a storytelling and trailer-planning agent will allow users to explore customized narratives and styles. It will be powered by a large language model for narrative generation and diffusion-based video models, making it a specialist in personalized cinematic creation.

**User Interface**
There is no specific folder for the UI in this repo, as it is in a separate git repo.
- The UI With Dummy Data is available at: [https://tarantaino-mockup.vercel.app/](https://tarantaino-mockup.vercel.app/)
- The Git Repo for the UI is available at: [https://github.com/kvrancic/tarantaino-mockup](https://github.com/kvrancic/tarantaino-mockup)
   
**Data**
We gathered a dataset of 11 million computed tag-movie relevance scores from a pool of 1,100 tags applied to 10,000 movies. The dataset, approximately 41MB in size, was collected from the following sources: "MovieLens Tag Genome Dataset 2014" in `https://grouplens.org/datasets/movielens/` . We have stored it in a private Google Cloud Bucket (see Data Pipeline Containers section below for setup instructions).

**Notebooks**
These folders contain code that is not part of container - for e.g: Application mockup, EDA, any 🔍 🕵️‍♀️ 🕵️‍♂️ crucial insights, reports or visualizations.

-> **EDA notebook**
From `notebooks/eda.ipynb`, we performed exploratory data analysis (EDA) on the dataset to understand its structure and content. You can create a venv to run the notebook running `bash notebooks/venv_setup.sh`, then `source notebooks/taraintino_env/bin/activate`. 
The EDA revealed that:
- The dataset contains a rich variety of tags associated with movies.
- We can identify popular tags and movies based on their relevance scores.
- Since the dataset is really small, there is no real utility in doing PCA, but we might be interested in looking at the effect of it on the results if time permits in this project. Indeed, we notice systematically that there are more irrelevant movie-tag pairs than relevant ones, more unpopular movies than popular ones, and more unused tags than popular ones. 

**Google cloud setup**
Make sure you have gcloud set up on your machine before working with the following containers.
- You should be outside of any virtual environment.
- Check in your terminal with `which gcloud`.
- If not, run `brew install --cask google-cloud-sdk`.
- Restart you terminal or run
`source "$(brew --prefix)/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.zsh.inc"`
`source "$(brew --prefix)/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/completion.zsh.inc"`
- Run `gcloud auth application-default login` to authenticate to your gcloud account.
- Run `nano ~/.zshrc` to open your shell config.
- Add this line at the end of the file `export GOOGLE_APPLICATION_CREDENTIALS="your_local_path/tarantAIno/secrets/llm-service-account.json"`.
- Exit (Ctrl + O, Enter, Ctrl + X) and run `source ~/.zshrc` to refresh your shell.
You are now ready to run the containers below.

# Data Pipeline and Quiz Service

This repo hosts the **data ingestion** (GCS ➜ ChromaDB) and the **preference-quiz API** (FastAPI).  
Follow the steps below to reproduce the pipeline end-to-end and play the quiz from your terminal.

## 1) Repository Layout


```bash
.
├── README.md
├── docker-compose.yml
├── MS2/
│   ├── hand-ins/
│   │   ├── references/
│   │   └── reports/
│   └── notebooks/
│       ├── requirements.txt
│       ├── venv_setup.sh
│       └── eda.ipynb
└── src/
    ├── datapipeline/
    │   ├── logs/                
    │   ├── downloader.py 
    │   └── uploader.py           
    ├── quiz_service/
    │   ├── api.py                
    │   ├── config.py              
    │   ├── model.py              
    │   ├── state.py
    │   ├── schemas.py
    │   └── utils.py
    ├── Dockerfile                
    ├── docker-shell.sh
    └── pyproject.toml
```


## 2) Code Files Description

| File | Description |
| :--- | :--- |
| `src/datapipeline/uploader.py` | **Uploads a local directory (e.g., dataset files) to a specified Google Cloud Storage (GCS) bucket/prefix.** |
| `src/datapipeline/downloader.py` | **Downloads data from GCS and handles ingestion:** it prepares movie-tag relevance data and tag metadata, storing both as vectors/records in the **ChromaDB** vector database. |
| `src/quiz_service/config.py` | **Manages core service configuration,** including Chroma connection, collection names, predefined quiz tags, and cached loading of prior mean/covariance NumPy arrays. |
| `src/quiz_service/model.py` | **Implements the Bayesian preference update logic** (`FullCovarianceTasteModel`) to refine the user's taste vector based on sequential tag-preference quiz answers. |
| `src/quiz_service/schemas.py` | **Defines data structures** (using Pydantic `BaseModel`) for all API requests and responses (e.g., `StartRequest`, `Question`, `AnswerResponse`) to ensure data validation. |
| `src/quiz_service/state.py` | **Manages in-memory session state** (`InMemoryStore`) to link a user's session ID with their active `FullCovarianceTasteModel` instance, providing session persistence. |
| `src/quiz_service/utils.py` | **Provides utility functions** for the quiz service: computes and saves the **prior mean/covariance** from Chroma embeddings, and calculates **top-N recommendations** via cosine similarity. |
| `src/quiz_service/api.py` | **The main FastAPI application:** exposes endpoints (`/quiz/start`, `/quiz/answer`, `/recommend`) to manage the user's quiz session and generate movie recommendations using the updated taste vector. |


## 3) Run the Code


Below are the full instructions to:  
1) upload and download data from GCS  
2) populate ChromaDB  
3) start the quiz  
4) get recommendations

The commands assume macOS or Linux with Docker, Python 3.10+, and `gcloud` installed.

---

# 3.1) Build and Start the Docker Services

From the project root directory:

```bash
docker compose build
docker compose up -d
```

This starts:

- chroma (vector database)
- rag-app (datapipeline environment)
- quiz-service (FastAPI backend)

# 3.2) Run the Datapipeline

For this part, make sure that the Google Cloud service account secret key is stored in `secrets/llm-service-account.json`.

For your reference, to upload your dataset to GCS:

```bash
docker compose exec -T app /opt/venv/bin/python -m datapipeline.uploader \
  --local_dir /app/data/tag_genome \
  --bucket tag-genome-data \
  --prefix datasets/tag_genome
```
Download the dataset from GCS into the container and populate ChromaDB with embeddings:

```bash
docker compose exec -T app /opt/venv/bin/python -m datapipeline.downloader \
  --to_chroma \
  --bucket tag-genome-data \
  --object_name datasets/tag_genome/tag_relevance.dat \
  --movies_object_name datasets/tag_genome/movies.dat \
  --collection movie_tag_relevance_cos

docker compose exec -T app /opt/venv/bin.python -m datapipeline.downloader \
  --to_tagmeta \
  --bucket tag-genome-data \
  --tags_object_name datasets/tag_genome/tags.dat \
  --tagmeta_collection tag_metadata
```

# 3.3) Use the Quiz API from Your Terminal

Start a Quiz Session:

```bash
SESSION_JSON=$(curl -s -X POST http://localhost:8082/quiz/start \
    -H 'content-type: application/json' \
    -d '{"num_questions":5}')

echo "$SESSION_JSON" | jq .
```

Extract IDs:

```bash
SESSION_ID=$(jq -r '.session_id' <<< "$SESSION_JSON")
QID=$(jq -r '.question.question_id' <<< "$SESSION_JSON")
```

Answer questions in loop (for testing):

```bash
for i in {1..5}; do
  RESP=$(curl -s -X POST http://localhost:8082/quiz/answer \
      -H 'content-type: application/json' \
      -d "{\"session_id\":\"$SESSION_ID\",\"question_id\":$QID,\"answer\":8}")

  echo "$RESP" | jq .

  STATUS=$(jq -r '.status' <<< "$RESP")
  [[ "$STATUS" == "complete" ]] && break

  QID=$(jq -r '.next_question.question_id' <<< "$RESP")
done
```

Get movie recommendations:

```bash
curl -s -X POST http://localhost:8082/recommend \
    -H 'content-type: application/json' \
    -d "{\"session_id\":\"$SESSION_ID\",\"top_n\":10}" | jq .
```

# 3.4) Frontend Integration

The quiz-vector service is designed to work with the TarAIntino frontend. The frontend:

1. Calls `POST /quiz/start` when the user opens the quiz page
2. Displays the returned `tag_label` and collects a 1-10 rating
3. Calls `POST /quiz/answer` with the rating to get the next question
4. Repeats until `status: "complete"` is returned
5. Stores the `session_id` for the backend pipeline to retrieve recommendations

**Environment Configuration:**

The frontend expects the quiz service at:
- Local development: `http://localhost:8082`
- Docker deployment: `http://quiz-service:8082`

**CORS:**

The API allows all origins for development. In production, restrict this in `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    ...
)
```

# 3.5) Restart if needed

```bash
docker compose down
```