#### Project Milestone 2 Organization

```
├── README.md
├── docker-compose.yml
├── notebooks
│   └── eda.ipynb
├── references
├── reports
│   └── TarAIntino AI Movie Generation Infrastructure.pdf
└── src
    ├── datapipeline
    │   ├── Dockerfile
    │   ├── Pipfile
    │   ├── Pipfile.lock
    │   ├── dataloader.py
    │   ├── docker-shell.sh
    │   ├── preprocess_rag.py
    │   └── pyproject.toml
    └── models
        ├── Dockerfile
        ├── docker-shell.sh
        ├── infer_model.py
        ├── model_rag.py
        ├── train_model.py
        └── pyproject.toml
```

To set up the venv for this project, run the following command: `bash venv_setup.sh`
Then activate the environment using: `source taraintino_env/bin/activate`

# AC215 - Milestone2 - TarAIntino

**Team Members**
Mathilde Cros, Robert Debbas, Maddy Jin, Karlo Vranci

**Group Name**
TarAIntino

**Project**
In this project, we aim to develop an avant-garde end-to-end AI movie trailer generation application. The app will feature an adaptive, Akinator-style quiz to elicit user preferences and include a modular pipeline connecting those preferences to generative APIs. Users can simply answer a short interactive quiz, and the app will produce a personalized, AI-generated movie trailer that reflects their cinematic taste. Additionally, a storytelling and trailer-planning agent will allow users to explore customized narratives and styles. It will be powered by a large language model for narrative generation and diffusion-based video models, making it a specialist in personalized cinematic creation.

### Milestone2 ###

In this milestone, we have the components for data management, including versioning, as well as the computer vision and language models.

**Data**
We gathered a dataset of 11 million computed tag-movie relevance scores from a pool of 1,100 tags applied to 10,000 movies. The dataset, approximately 41MB in size, was collected from the following sources: "MovieLens Tag Genome Dataset 2014" in `https://grouplens.org/datasets/movielens/` . We have stored it in a private Google Cloud Bucket.

From `notebooks/eda.ipynb`, we performed exploratory data analysis (EDA) on the dataset to understand its structure and content. The EDA revealed that:
- the dataset contains a rich variety of tags associated with movies
- we can identify popular tags based on their relevance scores
- We can keep a subset of the tags only, by looking at the most popular ones AND the correlated tags' relevance scores to remove duplicates (e.g. "witch", "witches", "wizards") to ask more diverse questions to the user.

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

**Data Pipeline Containers**
1. The data container pulls the MovieLens Tag Genome dataset from our private Google Cloud Storage bucket (defaults: bucket `tag-genome-data`, prefix `datasets/tag_genome`).
2. After download, it parses the raw `.dat` files (`movies.dat`, `tags.dat`, `tag_relevance.dat`), filters by relevance threshold, and aggregates the tag relevance scores into a compact JSONL dataset for downstream consumption.

**`src/datapipeline/preprocess_rag.py`**
   Orchestrates the end-to-end ingestion: downloads from GCS (if needed), inflates archives, parses MovieLens `.dat` artefacts or CSVs, filters by relevance threshold, and writes processed artefacts plus lineage metadata under `/data`.

**`src/datapipeline/dataloader.py`**
   Provides the reusable GCS download helper. It is invoked automatically by `preprocess_rag.py`, but can also be executed on its own for ad-hoc pulls (e.g., `python3 src/datapipeline/dataloader.py --bucket "$GCS_BUCKET" --prefix "$GCS_PREFIX" --out_dir local_raw`).

**Models container**
- `src/models/model_rag.py` consumes `/data/processed/movies.jsonl` and `/data/queries/sample_query.json`, performs a tag-overlap ranking, and emits `/outputs/recommendations.json` plus `/outputs/artifacts/inference_log.json`.

**Notebooks/Reports**
This folder contains code that is not part of container - for e.g: Application mockup, EDA, any 🔍 🕵️‍♀️ 🕵️‍♂️ crucial insights, reports or visualizations.

## Container Pipeline Demo

- **Configure secrets & environment**:
  - Place your service account key at `secrets/llm-service-account.json` (or adjust `GOOGLE_APPLICATION_CREDENTIALS` in `docker-compose.yml`).
  - Export the bucket/prefix before running, e.g.:
    ```
    export GCS_BUCKET=tag-genome-data
    export GCS_PREFIX=datasets/tag_genome
    # optional throttles
    export TAG_RELEVANCE_THRESHOLD=0.75
    export MAX_MOVIES=500
    export MAX_TAGS_PER_MOVIE=25
    ```
    You can also store these in a `.env` file; docker compose will pick them up automatically.
- **One-command run**: From the repo root execute `docker compose up --build`. Docker builds the two images and runs them sequentially. Typical log snippets:
  - `[LOAD …] DOWNLOADED gs://tag-genome-data/datasets/tag_genome/tag_relevance.dat → /data/raw/tag_relevance.dat`
  - `[DATA …] Wrote 500 documents → /data/processed/movies.jsonl`
  - `[MODEL …] Wrote recommendations → /outputs/recommendations.json`
- **Dependencies via uv**: Both Dockerfiles bootstrap `uv`; the `pyproject.toml` files in `src/datapipeline/` and `src/models/` declare the per-container dependencies (`google-cloud-storage`, `tqdm`, `pandas`, etc.).
- **Outputs / evidence**: After the compose run, inspect the named volumes:
  - `docker compose run --rm data-pipeline ls /data` → lists `raw/`, `processed/`, `queries/`, `artifacts/`.
  - `docker compose run --rm model-pipeline ls /outputs` → lists `recommendations.json` plus `artifacts/inference_log.json`.
  - Save run logs via `docker compose logs data-pipeline model-pipeline > data2/docker-compose-run.log`.
  - For submission, we staged a snapshot of inputs/outputs/logs under `data2/` (including `raw/`, `processed/`, `queries/`, `artifacts/`, `outputs/`, `output_artifacts/`, and the captured log file).
- **Cleanup**: `docker compose down --volumes --remove-orphans` removes the containers, shared volumes (`shared-data`, `model-outputs`), and networks once evidence is collected.
- **Local dry-run (optional)**: With credentials available locally, run `PYTHONPATH=src GCS_BUCKET=... GCS_PREFIX=... python -m datapipeline.preprocess_rag` followed by `PYTHONPATH=src PROCESSED_DATA_DIR=... python -m models.model_rag` to mirror the compose flow without containers. Outputs land under the directories you specify (e.g., `local_data/`).
