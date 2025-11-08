from pathlib import Path
from google.cloud import storage
from tqdm import tqdm
import argparse, os, time, json, re
import chromadb
from collections import defaultdict
from typing import Optional


def get_chroma_client():
    host = os.getenv("CHROMA_SERVER_HOST")
    port = os.getenv("CHROMA_SERVER_PORT")
    if host and port:
        return chromadb.HttpClient(host=host, port=int(port))
    # fallback for local dev
    path = os.getenv("CHROMA_PATH", "./chroma_db")
    return chromadb.PersistentClient(path=path)

def log(msg: str):
    print(f"[LOAD  {time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def download_prefix(bucket_name: str, prefix: str, out_dir: str):
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))
    if not blobs:
        log(f"No objects under gs://{bucket_name}/{prefix}")
        return
    log(f"Downloading {len(blobs)} objects → {out}")
    for b in tqdm(blobs, desc="Downloading"):
        rel = b.name[len(prefix):].lstrip("/") if b.name.startswith(prefix) else b.name
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        b.download_to_filename(str(dest))
        log(f"DOWNLOADED gs://{bucket_name}/{b.name} → {dest}")

def stream_object(bucket_name: str, object_name: str) -> bytes:
    client = storage.Client()
    blob = client.bucket(bucket_name).blob(object_name)
    data = blob.download_as_bytes()
    log(f"STREAMED {len(data)} bytes from gs://{bucket_name}/{object_name}")
    return data  # caller can parse CSV/JSON etc.

_SPLIT_RE = re.compile(r"\s*\|\|\s*|\t|,|\s+")

def parse_lines(raw: bytes):
    """
    Yields (movie_id:int, tag_id:int, relevance:float) from raw bytes.
    Skips empty / header-like lines.
    Accepts '||', tab, comma, or whitespace as separators.
    """
    for line in raw.decode("utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s:
            continue
        # Heuristic: skip a header row if present
        if s.lower().startswith("movie") and ("tag" in s.lower()):
            continue
        parts = _SPLIT_RE.split(s)
        if len(parts) < 3:
            continue
        try:
            movie_id = int(parts[0])
            tag_id = int(parts[1])
            rel = float(parts[2])
        except ValueError:
            # Malformed line; skip
            continue
        yield movie_id, tag_id, rel

def parse_movies(raw_bytes: bytes):
    """
    Parse movies.dat style lines:
    movie_id \t title \t (maybe tmdbId or other numeric id)
    Returns dict {movie_id: title_str}
    """
    out = {}
    for line in raw_bytes.decode("utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s:
            continue
        parts = s.split("\t")
        if len(parts) < 2:
            continue
        try:
            mid = int(parts[0])
        except ValueError:
            # skip headers if any
            continue
        title = parts[1].strip()
        out[mid] = title
    return out

def parse_tags(raw_bytes: bytes):
    """
    Parse tags.dat style lines:
    <tag_id>\t<tag_name>\t<count>

    Returns dict {tag_id: tag_name}
    We ignore the count.
    """
    out = {}
    for line in raw_bytes.decode("utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s:
            continue
        parts = s.split("\t")
        if len(parts) < 2:
            continue
        try:
            tid = int(parts[0])
        except ValueError:
            # skip headers if any
            continue
        name = parts[1].strip()
        out[tid] = name
    return out


def ingest_tag_relevance_to_chroma(
    bucket: str,
    object_name: str,                # tag_relevance.dat
    chroma_path: str = "./chroma_db",
    collection_name: str = "movie_tag_relevance_cos",
    batch_size: int = 2000,
    movies_object_name: Optional[str] = None,  # NEW
):
    """
    Ingests tag_relevance.dat from GCS directly into Chroma.

    - One item per movie (id=str(movie_id))
    - Embedding = vector over all tagIDs (index order saved to tag_index.json)
    - metadata={"movieId": movie_id}
    """
    log("Fetching tag_relevance.dat from GCS…")
    raw = stream_object(bucket, object_name)

    log("First pass: collecting unique tags & sparse rows per movie…")
    # Sparse store: movie_id -> dict(col_index -> relevance) [but we cannot set col yet]
    # So first we must collect set of tag_ids, and temporarily keep per-movie as {tag_id: relevance}
    tag_ids = set()
    movie_to_sparse = defaultdict(dict)

    n_lines = 0
    for movie_id, tag_id, rel in parse_lines(raw):
        movie_to_sparse[movie_id][tag_id] = rel
        tag_ids.add(tag_id)
        n_lines += 1
    log(f"Parsed {n_lines:,} triples across {len(movie_to_sparse):,} movies and {len(tag_ids):,} unique tags.")

    # Create stable tag index (sorted by tag_id)
    tag_ids_sorted = sorted(tag_ids)
    tag_to_col = {tid: i for i, tid in enumerate(tag_ids_sorted)}
    dim = len(tag_ids_sorted)
    log(f"Vector dimension = number of unique tags = {dim:,}")

    # Ensure persistence directory exists and save tag index
    log_dir = Path(os.getenv("LOG_DIR", "./src/datapipeline/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    tag_index_path = log_dir / f"{collection_name}__tag_index.json"
    with tag_index_path.open("w", encoding="utf-8") as f:
        json.dump({"tag_ids_sorted": tag_ids_sorted}, f)
    log(f"Saved tag index mapping → {tag_index_path}")
    
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        log(f"Using existing Chroma collection: {collection_name}")
    except Exception:
        collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"} 
        )
        log(f"Created Chroma collection (cosine): {collection_name}")

    # Batch insert
    movie_ids_sorted = sorted(movie_to_sparse.keys())
    log(f"Ingesting into Chroma in batches of {batch_size} movies…")

    def dense_from_sparse(sparse_map):
        # Create a dense vector of length dim; fill only non-zeros
        vec = [0.0] * dim
        for t_id, val in sparse_map.items():
            j = tag_to_col.get(t_id)
            if j is not None:
                vec[j] = float(val)
        return vec
    

    # Get titles if provided    
    movie_titles = {}
    if movies_object_name is not None:
        log(f"Fetching {movies_object_name} from GCS for titles…")
        raw_movies = stream_object(bucket, movies_object_name)
        movie_titles = parse_movies(raw_movies)
        log(f"Parsed {len(movie_titles)} movie titles.")

    batch_ids, batch_embeds, batch_metas = [], [], []
    total = 0

    for m_id in tqdm(movie_ids_sorted, desc="Chroma add"):
        vec = dense_from_sparse(movie_to_sparse[m_id])
        batch_ids.append(str(m_id))
        batch_embeds.append(vec)

        title = movie_titles.get(m_id, f"Movie {m_id}")
        batch_metas.append({"movieId": m_id, "title": title})

        if len(batch_ids) >= batch_size:
            collection.add(ids=batch_ids, embeddings=batch_embeds, metadatas=batch_metas)
            total += len(batch_ids)
            batch_ids, batch_embeds, batch_metas = [], [], []

    # Flush tail
    if batch_ids:
        collection.add(ids=batch_ids, embeddings=batch_embeds, metadatas=batch_metas)
        total += len(batch_ids)

    log(f"Inserted {total:,} movie vectors into Chroma collection '{collection_name}'.")
    log("DONE")

def ingest_tags_metadata_to_chroma(
    bucket: str,
    tags_object_name: str,                 # e.g. "datasets/tag_genome/tags.dat"
    collection_name: str = "tag_metadata"
):
    """
    Create/update a Chroma collection mapping tag IDs -> human-readable tag names.

    We store:
      id = str(tag_id)
      metadata = {"tagId": tag_id, "name": "dark", "count": <optional> }

    No embeddings here. This is just a lookup/metadata collection.
    To satisfy Chroma's API, we'll store a tiny dummy embedding (like [0.0]).
    That keeps the interface uniform.
    """

    log(f"Fetching {tags_object_name} from GCS for tag metadata…")
    raw = stream_object(bucket, tags_object_name)
    tag_map = parse_tags(raw)  # dict {tid:int -> name:str}
    log(f"Parsed {len(tag_map)} tags.")

    client = get_chroma_client()
    # Try get or create the collection
    try:
        col = client.get_collection(collection_name)
        log(f"Using existing Chroma collection: {collection_name}")
    except Exception:
        col = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # doesn't really matter here
        )
        log(f"Created Chroma collection: {collection_name}")

    # We'll insert/update in batches
    batch_ids, batch_embeds, batch_metas = [], [], []
    total = 0

    for tid, name in tag_map.items():
        batch_ids.append(str(tid))
        # dummy 1-dim embedding so Chroma is happy
        batch_embeds.append([0.0])
        batch_metas.append({
            "tagId": tid,
            "name": name
        })

        if len(batch_ids) >= 500:
            col.add(
                ids=batch_ids,
                embeddings=batch_embeds,
                metadatas=batch_metas
            )
            total += len(batch_ids)
            batch_ids, batch_embeds, batch_metas = [], [], []

    # flush tail
    if batch_ids:
        col.add(
            ids=batch_ids,
            embeddings=batch_embeds,
            metadatas=batch_metas
        )
        total += len(batch_ids)

    log(f"Inserted {total} tag metadata rows into Chroma collection '{collection_name}'.")
    log("DONE")


def cli():
    ap = argparse.ArgumentParser(description="Load from GCS or ingest tag_relevance.dat into Chroma")
    ap.add_argument("--bucket", default=os.getenv("GCS_BUCKET"))
    ap.add_argument("--prefix", default=os.getenv("GCS_PREFIX", "datasets/tag_genome"))
    ap.add_argument("--out_dir", default="data")
    ap.add_argument("--stream_object", default=None, help="gs object name to stream")
    ap.add_argument("--to_chroma", action="store_true", help="If set, ingest tag_relevance.dat into Chroma")
    ap.add_argument("--object_name", default=os.getenv("TAG_REL_OBJECT", "datasets/tag_genome/tag_relevance.dat"),
                    help="GCS object name for tag_relevance.dat")
    ap.add_argument("--chroma_path", default=os.getenv("CHROMA_PATH", "./chroma_db"))
    ap.add_argument("--movies_object_name", default=os.getenv("MOVIES_OBJECT", "datasets/tag_genome/movies.dat"),
                    help="GCS object name for movies.dat (to pull titles)")
    ap.add_argument("--to_tagmeta", action="store_true",
        help="If set, ingest tags.dat into a tag_metadata collection")
    ap.add_argument("--tags_object_name", default=os.getenv("TAGS_OBJECT", "datasets/tag_genome/tags.dat"),
        help="GCS object name for tags.dat")
    ap.add_argument("--tagmeta_collection", default=os.getenv("TAGMETA_COLLECTION", "tag_metadata"),
        help="Chroma collection name for tag metadata")
    ap.add_argument("--collection", default=os.getenv("CHROMA_COLLECTION", "movie_tag_relevance_cos"))
    ap.add_argument("--batch_size", type=int, default=int(os.getenv("BATCH_SIZE", "2000")))
    args = ap.parse_args()

    assert args.bucket, "Set --bucket or GCS_BUCKET"

    if args.to_chroma:
        # Movie embeddings ingest
        ingest_tag_relevance_to_chroma(
            bucket=args.bucket,
            object_name=args.object_name,
            chroma_path=args.chroma_path,
            collection_name=args.collection,
            batch_size=args.batch_size,
            movies_object_name=args.movies_object_name
        )

    elif args.to_tagmeta:
        # Tag metadata ingest
        ingest_tags_metadata_to_chroma(
            bucket=args.bucket,
            tags_object_name=args.tags_object_name,
            collection_name=args.tagmeta_collection
        )

    elif args.stream_object:
        _ = stream_object(args.bucket, args.stream_object)
        log("DONE")

    else:
        download_prefix(args.bucket, args.prefix, args.out_dir)
        log("DONE")

if __name__ == "__main__":
    cli()


####################
# BUILD YOUR IMAGE #
####################

# docker build -t rag-pipeline -f src/datapipeline/Dockerfile .

######################
# RUN YOUR CONTAINER #
######################

# src/datapipeline/docker-shell.sh

############################################################################################
# EXECUTE WITHIN YOUR CONTAINER TO DOWNLOAD DATA FROM GCS AND STORE IN THE VECTOR DATABASE #
############################################################################################

# python datapipeline/dataloader.py --to_chroma 
#                                   --bucket "$GCS_BUCKET" 
#                                   --object_name "$TAG_REL_OBJECT" 
#                                   --collection "$CHROMA_COLLECTION"
