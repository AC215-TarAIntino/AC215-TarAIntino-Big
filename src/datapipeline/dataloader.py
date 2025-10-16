from pathlib import Path
from google.cloud import storage
from tqdm import tqdm
import argparse
import os
import time


def log(msg: str) -> None:
    print(f"[LOAD  {time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def download_prefix(bucket_name: str, prefix: str, out_dir: str) -> None:
    """Download every object under the prefix into out_dir, mirroring sub-paths."""
    out_path = Path(out_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))
    if not blobs:
        log(f"No objects found under gs://{bucket_name}/{prefix}")
        return

    log(f"Downloading {len(blobs)} objects → {out_path}")
    for blob in tqdm(blobs, desc="Downloading"):
        rel_name = (
            blob.name[len(prefix):].lstrip("/")
            if blob.name.startswith(prefix)
            else blob.name
        )
        dest = out_path / rel_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(dest))
        log(f"DOWNLOADED gs://{bucket_name}/{blob.name} → {dest}")


def stream_object(bucket_name: str, object_name: str) -> bytes:
    client = storage.Client()
    blob = client.bucket(bucket_name).blob(object_name)
    data = blob.download_as_bytes()
    log(f"STREAMED {len(data)} bytes from gs://{bucket_name}/{object_name}")
    return data


def cli() -> None:
    parser = argparse.ArgumentParser(description="Load data from Google Cloud Storage")
    parser.add_argument("--bucket", default=os.getenv("GCS_BUCKET"))
    parser.add_argument("--prefix", default=os.getenv("GCS_PREFIX", "datasets/tag_genome"))
    parser.add_argument("--out_dir", default=os.getenv("RAW_DATA_DIR", "/data/raw"))
    parser.add_argument("--stream_object", default=None)
    args = parser.parse_args()

    assert args.bucket, "Set --bucket or GCS_BUCKET"
    if args.stream_object:
        _ = stream_object(args.bucket, args.stream_object)
    else:
        download_prefix(args.bucket, args.prefix, args.out_dir)
    log("DONE")


def main() -> None:
    cli()


####################
# BUILD YOUR IMAGE #
####################

# docker build -t rag-pipeline -f src/datapipeline/Dockerfile .

######################
# RUN YOUR CONTAINER #
######################

# src/datapipeline/docker-shell.sh

##############################################################################
# EXECUTE NECESSARY COMMANDS WITHIN YOUR CONTAINER TO DOWNLOAD DATA FROM GCS #
##############################################################################
# Example:
# python datapipeline/dataloader.py --bucket "$GCS_BUCKET" --prefix "$GCS_PREFIX" --out_dir /app/data
