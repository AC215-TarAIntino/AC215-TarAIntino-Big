from pathlib import Path
from google.cloud import storage
from tqdm import tqdm
import argparse, os, time

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

def cli():
    ap = argparse.ArgumentParser(description="Load from GCS")
    ap.add_argument("--bucket", default=os.getenv("GCS_BUCKET"))
    ap.add_argument("--prefix", default=os.getenv("GCS_PREFIX", "datasets/tag_genome"))
    ap.add_argument("--out_dir", default="data")
    ap.add_argument("--stream_object", default=None)
    args = ap.parse_args()
    assert args.bucket, "Set --bucket or GCS_BUCKET"
    if args.stream_object:
        _ = stream_object(args.bucket, args.stream_object)
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

###########################################################
# EXECUTE WITHIN YOUR CONTAINER TO DOWNLOAD DATA FROM GCS #
###########################################################

# python datapipeline/dataloader.py --bucket "$GCS_BUCKET" --prefix "$GCS_PREFIX" --out_dir /app/data