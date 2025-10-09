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

# AC215 - Milestone2 - TarAIntino

**Team Members**
Mathilde Cros, Robert Debbas, Maddy Jin, Karlo Vranci

**Group Name**
TarAIntino

**Project**
In this project, we aim to develop an ... application. The app will feature ... and include a ... . Users can simply ..., and the app will ... . Additionally, ... will allow users to ... . It will be powered by a ... model and ... models, making it a specialist in ... .


### Milestone2 ###

In this milestone, we have the components for data management, including versioning, as well as the computer vision and language models.

**Data**
We gathered a dataset of #nbr images representing approximately ... different movies. The dataset, approximately 100GB in size, was collected from the following sources: ... . We have stored it in a private Google Cloud Bucket.

**Data Pipeline Containers**
1. One container processes the ...GB dataset by resizing the images and storing them back to Google Cloud Storage (GCS).

	**Input:** Source and destination GCS locations, resizing parameters, and required secrets (provided via Docker).

	**Output:** Resized images stored in the specified GCS location.

2. Another container prepares data for the RAG model, including tasks such as chunking, embedding, and populating the vector database.


## Data Pipeline Overview

1. **`src/datapipeline/preprocess_cv.py`**
   This script handles preprocessing on our 100GB dataset. It reduces the image sizes to 128x128 (a parameter that can be changed later) to enable faster iteration during processing. The preprocessed dataset is now reduced to 10GB and stored on GCS.

2. **`src/datapipeline/preprocess_rag.py`**
   This script prepares the necessary data for setting up our vector database. It performs chunking, embedding, and loads the data into a vector database (ChromaDB).

3. **`src/datapipeline/Pipfile`**
   We used the following packages to help with preprocessing:
   - `special cheese package`

4. **`src/preprocessing/Dockerfile(s)`**
   Our Dockerfiles follow standard conventions, with the exception of some specific modifications described in the Dockerfile/described below.


## Running Dockerfile
Instructions for running the Dockerfile can be added here.
To run Dockerfile - `Instructions here`

**Models container**
- This container has scripts for model training, rag pipeline and inference
- Instructions for running the model container - `Instructions here`

**Notebooks/Reports**
This folder contains code that is not part of container - for e.g: Application mockup, EDA, any 🔍 🕵️‍♀️ 🕵️‍♂️ crucial insights, reports or visualizations.