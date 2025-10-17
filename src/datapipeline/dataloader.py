from pathlib import Path
from google.cloud import storage
from tqdm import tqdm
import argparse, os, time, json, re
import chromadb
from collections import defaultdict

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

def ingest_tag_relevance_to_chroma(
    bucket: str,
    object_name: str,
    chroma_path: str = "./chroma_db",
    collection_name: str = "movie_tag_relevance_cos",
    batch_size: int = 2000
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
    chroma_dir = Path(chroma_path)
    chroma_dir.mkdir(parents=True, exist_ok=True)
    tag_index_path = chroma_dir / f"{collection_name}__tag_index.json"
    with tag_index_path.open("w", encoding="utf-8") as f:
        json.dump({"tag_ids_sorted": tag_ids_sorted}, f)
    log(f"Saved tag index mapping → {tag_index_path}")

    client = chromadb.PersistentClient(path=str(chroma_dir))
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

    batch_ids, batch_embeds, batch_metas = [], [], []
    total = 0

    for m_id in tqdm(movie_ids_sorted, desc="Chroma add"):
        vec = dense_from_sparse(movie_to_sparse[m_id])
        batch_ids.append(str(m_id))
        batch_embeds.append(vec)
        batch_metas.append({"movieId": m_id})

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
    ap.add_argument("--collection", default=os.getenv("CHROMA_COLLECTION", "movie_tag_relevance_cos"))
    ap.add_argument("--batch_size", type=int, default=int(os.getenv("BATCH_SIZE", "2000")))
    args = ap.parse_args()

    assert args.bucket, "Set --bucket or GCS_BUCKET"

    if args.to_chroma:
        ingest_tag_relevance_to_chroma(
            bucket=args.bucket,
            object_name=args.object_name,
            chroma_path=args.chroma_path,
            collection_name=args.collection,
            batch_size=args.batch_size
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

# python datapipeline/dataloader.py --to_chroma \
#   --bucket "$GCS_BUCKET" \
#   --object_name "$TAG_REL_OBJECT" \
#   --chroma_path "$CHROMA_PATH" \
#   --collection "$CHROMA_COLLECTION" \
#   --batch_size "${BATCH_SIZE:-2000}"
