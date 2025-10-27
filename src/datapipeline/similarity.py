import os, random
from typing import List, Tuple, Optional
import chromadb

def get_chroma_client():
    host = os.getenv("CHROMA_SERVER_HOST")
    port = os.getenv("CHROMA_SERVER_PORT")
    if host and port:
        return chromadb.HttpClient(host=host, port=int(port))
    # fallback for local dev
    path = os.getenv("CHROMA_PATH", "./chroma_db")
    return chromadb.PersistentClient(path=path)

def similarity(
    *,
    movie_id: Optional[str] = None,
    embedding: Optional[List[float]] = None,
    n: int = 5,
    chroma_path: str = "./chroma_db",
    collection_name: str = "movie_tag_relevance_cos",  # or *_cos if you reingested with cosine
) -> List[Tuple[str, float]]:
    if (movie_id is None) == (embedding is None):
        raise ValueError("Provide exactly one of movie_id or embedding.")

    client = get_chroma_client()
    col = client.get_collection(collection_name)

    if movie_id is not None:
        got = col.get(ids=[str(movie_id)], include=["embeddings"])
        if not got.get("embeddings"):
            raise ValueError(f"No embedding for movie {movie_id}")
        q = got["embeddings"][0]
    else:
        q = embedding

    res = col.query(query_embeddings=[q], n_results=n, include=["distances"])
    ids = res["ids"][0]
    dists = res["distances"][0]
    sims = [1.0 - d for d in dists]  # correct if collection metric = cosine
    return list(zip(ids, sims))

if __name__ == "__main__":
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    preferred = os.getenv("CHROMA_COLLECTION", "movie_tag_relevance_cos")
    fallback = "movie_tag_relevance_cos"

    client = get_chroma_client()
    try:
        col = client.get_collection(preferred); collection_name = preferred
    except Exception:
        col = client.get_collection(fallback); collection_name = fallback

    sample = col.peek(1)
    embs = sample.get("embeddings", None)
    dim = len(embs[0]) if embs is not None and len(embs) > 0 else 1128

    print(f"[info] Using collection: {collection_name}")
    print(f"[info] Collection dimension: {dim}")

    dummy = [random.random() for _ in range(dim)]
    for mid, s in similarity(embedding=dummy, n=5,
                             chroma_path=chroma_path,
                             collection_name=collection_name):
        print(f"Movie {mid}: similarity {s:.4f}")

####################
# BUILD YOUR IMAGE #
####################

# docker build -t rag-pipeline -f src/datapipeline/Dockerfile .

######################
# RUN YOUR CONTAINER #
######################

# src/datapipeline/docker-shell.sh

##################################################################################
# EXECUTE WITHIN YOUR CONTAINER TO COMPUTE THE COSINE SIMILARITY SEARCH FUNCTION #
##################################################################################

# python datapipeline/similarity.py
