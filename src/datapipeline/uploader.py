import os, argparse
from pathlib import Path
from google.cloud import storage
from tqdm import tqdm
import time

def log(msg: str):
    print(f"[STORE {time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def upload_dir(local_dir: str, bucket_name: str, prefix: str = ""):
    local = Path(local_dir).expanduser().resolve()
    files = [p for p in local.rglob("*") if p.is_file()]
    if not files:
        log(f"No files found in {local}")
        return

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    log(f"Uploading {len(files)} files → gs://{bucket_name}/{prefix}")
    for p in tqdm(files, desc="Uploading"):
        rel = p.relative_to(local).as_posix()
        blob_name = f"{prefix.rstrip('/')}/{rel}" if prefix else rel
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(p))
        log(f"UPLOADED {p} → gs://{bucket_name}/{blob_name}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local_dir", required=True)
    ap.add_argument("--bucket", default=os.getenv("GCS_BUCKET"))
    ap.add_argument("--prefix", default=os.getenv("GCS_PREFIX", "datasets/tag_genome"))
    args = ap.parse_args()
    assert args.bucket, "Set --bucket or GCS_BUCKET"
    upload_dir(args.local_dir, args.bucket, args.prefix)

if __name__ == "__main__":
    main()
