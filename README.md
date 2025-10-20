#### Project Milestone 2 Organization

```
├── README.md
├── docker-compose.yml
├── notebooks
    ├── requirements.txt
    ├── venv_setup.sh
│   └── eda.ipynb
├── hand-ins
│  ├── references
│  └── reports
│      └── TarAIntino AI Movie Generation Infrastructure.pdf
└── src
    ├── datapipeline
    │   ├── logs/
    │   ├── chroma_db/
    │   ├── Dockerfile
    │   ├── dataloader.py
    │   ├── docker-shell.sh
    │   ├── preprocess_rag.py
    │   └── pyproject.toml
    ├── llm
    │   ├── logs/
    │   ├── Dockerfile
    │   ├── prompting.py
    │   ├── docker-shell.sh
    │   └── pyproject.toml
    └── models (empty for milestone 2)
        ├── Dockerfile
        ├── docker-shell.sh
        ├── infer_model.py
        ├── model_rag.py
        ├── train_model.py
        └── pyproject.toml
```

# AC215 - Milestone2 - TarAIntino

**Team Members**
Mathilde Cros, Robert Debbas, Maddy Jin, Karlo Vrancic

**Group Name**
TarAIntino

**Project**
In this project, we aim to develop an avant-garde end-to-end AI movie trailer generation application. The app will feature an adaptive, Akinator-style quiz to elicit user preferences and include a modular pipeline connecting those preferences to generative APIs. Users can simply answer a short interactive quiz, and the app will produce a personalized, AI-generated movie trailer that reflects their cinematic taste. Additionally, a storytelling and trailer-planning agent will allow users to explore customized narratives and styles. It will be powered by a large language model for narrative generation and diffusion-based video models, making it a specialist in personalized cinematic creation.

### Milestone2 ###

**Hand-ins**
This folder contains for the respective milestones:
- All reports in the `reports` folder.
   - The report for this milestone is `TarAIntino AI Movie Generation Infrastructure.pdf`.
- Any other documents are the `references` folder.
   - The graph of the architecture of the project is `TarAIntino System Architecture 1.jpeg` and `TarAIntino System Architecture 2.jpeg` (it was too big in one image).

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

**Data Pipeline Container**
1. From the nature of our data, we will not have much of a preprocessing step necessary.
2. A container prepares data for the RAG model, by populating the vector database and allows for computing similarity scores between movies.
3. Instructions for loading the data in your container can be found at the end of the dataloader.py, preprocess_rag.py and similarity.py files respectively.

**`src/datapipeline/preprocess_rag.py`**
   This script stores the data in the GCS bucket.

**`src/datapipeline/dataloader.py`**
   This script downloads the data from the GCS bucket, formats it to vectors and then stores it in the ChromaDB vector database.

**`src/datapipeline/similarity.py`**
   This script computes cosine similarity between movies embeddings from the ChromaDB vector database.

**Deliverables for Data Pipeline Container**
- The logs of running the above scripts can be found in the `src/datapipeline/logs` folder. 
- The ChromaDB database is stored in the `src/datapipeline/chroma_db` folder.

**LLM container**
1. A container to be able to chat/have access to a running llm (using vertex ai).
2. The **`src/llm/prompting.py`** file enables the access to a chat box to the LLM in your terminal.
3. To access it:
- Run `gcloud auth application-default login`
- Then, run `gcloud config set project llm-service-account-474620`
- IF you get the warning `ADC does not have the "serviceusage.services.use" permission on this project`, ask Robert Debbas for permission access before pursuing.
- Check with `gcloud config list`, you should see `project = llm-service-account-474620` and `account = your@email.com`
- Finally, check `gcloud services list --enabled | grep aiplatform` should return `aiplatform.googleapis.com`
- And check `gcloud auth application-default set-quota-project llm-service-account-474620`
- You are now ready to run the llm container in the instructions at the end of the `prompting.py` file.

**Deliverables for LLM Container**
- The logs of running the above prompting script can be found in the `src/llm/logs` folder. 

**Models container** --> Not necessary for milestone 2 yet (empty)
...