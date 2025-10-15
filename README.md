#### Project Milestone 2 Organization

```
├── Readme.md
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
    └── models
        ├── Dockerfile
        ├── docker-shell.sh
        ├── infer_model.py
        ├── model_rag.py
        └── train_model.py
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
1. From the nature of our data, we will not have a preprocessing step necessary.
2. A container prepares data for the RAG model, by embedding it and populating the vector database.

**`src/datapipeline/preprocess_rag.py`**
   This script prepares the necessary data for setting up our vector database. It performs embedding and loads the data into a vector database.

**`src/datapipeline/dataloader.py`**
   This script loads the (prepared) data from the Google Cloud Bucket.

## Running Dockerfile
Instructions for loading the data in your container can be found at the end of the dataloader.py file. Respectively for the preprocess_rag.py file.

**Models container** --> TO-DO !!
- This container has scripts for model training, rag pipeline and inference
- Instructions for running the model container - `Instructions here`

**Notebooks/Reports**
This folder contains code that is not part of container - for e.g: EDA, any 🔍 🕵️‍♀️ 🕵️‍♂️ crucial insights, reports or visualizations.

UI With Dummy Data is available at: [https://tarantaino-mockup.vercel.app/](https://tarantaino-mockup.vercel.app/)
The Git Repo for the UI is available at: [https://github.com/kvrancic/tarantaino-mockup](https://github.com/kvrancic/tarantaino-mockup)

