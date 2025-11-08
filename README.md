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

# Data Pipleine and Quiz Service

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
│   │       └── TarAIntino AI Movie Generation Infrastructure.pdf
│   └── notebooks/
│       ├── requirements.txt
│       ├── venv_setup.sh
│       └── eda.ipynb
└── src/
    ├── datapipeline/
    │   ├── logs/                 # prior_mean.npy, prior_cov.npy, tag index, etc.
    │   ├── downloader.py         # loads data from GCS to ChromaDB
    │   └── uploader.py           # uploads data to GCS
    ├── quiz_service/
    │   ├── api.py                # FastAPI app
    │   ├── config.py
    │   ├── model.py              # Bayesian preference update logic
    │   ├── state.py
    │   ├── schemas.py
    │   └── utils.py
    ├── Dockerfile                # base image for both app + quiz-service
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

# 3.1) Authenticate with Google Cloud

You must authenticate locally so that the datapipeline container can access the bucket.

```bash
gcloud auth application-default login
```

Check that authentication succeeded:

```bash
gcloud auth application-default print-access-token
```

If it prints a token, you're good.

Make sure your environment variable is set correctly:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="YOUR_PATH/tarantAIno/secrets/llm-service-account.json"
```

# 3.2) Build and Start the Docker Services

From the project root directory:

```bash
docker compose build
docker compose up -d
```

This starts:

- chroma (vector database)
- rag-app (datapipeline environment)
- quiz-service (FastAPI backend)

# 3.3) Run the Datapipeline

Upload your dataset to GCS:

```bash
docker exec -it rag-app bash
python3 datapipeline/uploader.py
```

Download the dataset from GCS into the container and populate ChromaDB with embeddings:

```bash
python3 datapipeline/downloader.py
```

# 3.4) Use the Quiz API from Your Terminal

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