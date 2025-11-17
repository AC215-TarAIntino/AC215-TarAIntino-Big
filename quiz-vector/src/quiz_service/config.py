import os
import chromadb
import numpy as np
from pathlib import Path
from functools import lru_cache

PRIOR_MEAN_PATH = os.getenv("PRIOR_MEAN_PATH", "/app/prior_mean.npy")
PRIOR_COV_PATH  = os.getenv("PRIOR_COV_PATH",  "/app/prior_cov.npy")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "movie_tag_relevance_cos")
TAG_INDEX_JSON = os.getenv(
    "TAG_INDEX_JSON",
    f"/app/logs/{CHROMA_COLLECTION}__tag_index.json"
)

# Same QUIZ_TAGS you used (UI-friendly)
QUIZ_TAGS = [
    (416, "funny"), (284, "dark"), (862, "romance"), (1084, "violent"),
    (496, "heartwarming"), (311, "disturbing"), (347, "emotional"),
    (1023, "thought-provoking"), (886, "sci-fi"), (267, "crime"),
    (376, "fantasy"), (18, "action"), (521, "horror"),
    (229, "comedy"), (322, "drama"), (688, "mystery"),
]

def get_chroma_client():
    host = os.getenv("CHROMA_SERVER_HOST")
    port = os.getenv("CHROMA_SERVER_PORT")
    if host and port:
        return chromadb.HttpClient(host=host, port=int(port))
    path = os.getenv("CHROMA_PATH", "./chroma_db")
    return chromadb.PersistentClient(path=path)

@lru_cache(maxsize=1)
def get_collection():
    return get_chroma_client().get_collection(CHROMA_COLLECTION)

def load_tagid2col(path: str):
    import json
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {tid: j for j, tid in enumerate(data["tag_ids_sorted"])}

@lru_cache(maxsize=1)
def get_tagid2col():
    return load_tagid2col(TAG_INDEX_JSON)

@lru_cache(maxsize=1)
def get_prior_mean() -> np.ndarray:
    return np.load(PRIOR_MEAN_PATH)

@lru_cache(maxsize=1)
def get_prior_cov() -> np.ndarray:
    return np.load(PRIOR_COV_PATH)