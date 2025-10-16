import csv
import gzip
import json
import os
import shutil
import time
import zipfile
from collections import defaultdict
from pathlib import Path
import pandas as pd
from typing import Dict, Iterable, List, Optional, Tuple

def log(message: str) -> None:
    print(f"[DATA {time.strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


def ensure_dirs(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def ensure_raw_data(raw_dir: Path, bucket: Optional[str], prefix: str) -> None:
    if any(raw_dir.glob("**/*")):
        log(f"Raw data already present in {raw_dir}, skipping download")
        return
    if not bucket:
        raise RuntimeError(
            f"No raw data found in {raw_dir} and GCS_BUCKET not set. "
            "Provide a bucket or pre-populate RAW_DATA_DIR."
        )
    log(f"Fetching raw data from gs://{bucket}/{prefix}")
    from . import dataloader  # local import to avoid requiring GCS deps when not needed

    dataloader.download_prefix(bucket, prefix, str(raw_dir))


def inflate_archives(raw_dir: Path) -> None:
    """Extract zip/gz archives so downstream steps can read plain CSV files."""
    for zip_path in sorted(raw_dir.rglob("*.zip")):
        target_dir = zip_path.with_suffix("")
        if target_dir.exists():
            continue
        log(f"Extracting {zip_path} → {target_dir}")
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(target_dir)
    for gz_path in sorted(raw_dir.rglob("*.csv.gz")):
        target_file = gz_path.with_suffix("")
        if target_file.exists():
            continue
        log(f"Decompressing {gz_path} → {target_file}")
        with gzip.open(gz_path, "rb") as src, target_file.open("wb") as dest:
            shutil.copyfileobj(src, dest)


def detect_csv_type(csv_path: Path) -> Optional[str]:
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
    except Exception:
        return None
    if not header:
        return None
    columns = {col.strip().lower() for col in header}
    if {"movie_id", "title", "tag", "relevance"} <= columns:
        return "flat"
    if {"movieid", "title", "tag", "relevance"} <= columns:
        return "flat"
    if {"movieid", "tagid", "relevance"} <= columns:
        return "scores"
    if {"tagid", "tag"} <= columns:
        return "tags"
    if {"movieid", "title"} <= columns:
        return "movies"
    return None


def collect_sources(raw_dir: Path) -> Dict[str, List[Path]]:
    categorized: Dict[str, List[Path]] = defaultdict(list)
    for csv_path in sorted(raw_dir.rglob("*.csv")):
        kind = detect_csv_type(csv_path)
        if kind:
            categorized[kind].append(csv_path)
    # Handle MovieLens `.dat` artefacts (tab-delimited, header lines defined in README)
    dat_map = {
        "tag_relevance": ("scores_dat", ["movieId", "tagId", "relevance"]),
        "tags": ("tags_dat", ["tagId", "tag"]),
        "movies": ("movies_dat", ["movieId", "title", "genres"]),
    }
    for name, (label, columns) in dat_map.items():
        path = raw_dir / f"{name}.dat"
        if path.exists():
            categorized[label].append((path, columns))
    return categorized


def load_tag_map(tag_path: Optional[Path]) -> Dict[str, str]:
    tag_map: Dict[str, str] = {}
    if not tag_path:
        return tag_map
    log(f"Loading tags map from {tag_path}")
    if isinstance(tag_path, tuple):
        file_path, columns = tag_path
        df = pd.read_csv(file_path, sep="\t", names=columns, engine="python")
        for _, row in df.iterrows():
            tag_map[str(row["tagId"])] = str(row["tag"])
    else:
        with tag_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                tag_id = str(row.get("tagId") or row.get("tagid"))
                tag_name = row.get("tag") or row.get("tagName")
                if tag_id and tag_name:
                    tag_map[tag_id] = tag_name
    return tag_map


def load_movie_titles(movie_path: Optional[Path]) -> Dict[str, str]:
    title_map: Dict[str, str] = {}
    if not movie_path:
        return title_map
    log(f"Loading movie titles from {movie_path}")
    if isinstance(movie_path, tuple):
        file_path, columns = movie_path
        df = pd.read_csv(file_path, sep="::", names=columns, engine="python", header=None)
        for _, row in df.iterrows():
            movie_id = str(row["movieId"])
            title = str(row["title"])
            if movie_id and title:
                title_map[movie_id] = title
    else:
        with movie_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                movie_id = str(row.get("movieId") or row.get("movie_id"))
                title = row.get("title")
                if movie_id and title:
                    title_map[movie_id] = title
    return title_map


def load_flat_dataset(
    csv_path: Path,
    threshold: float,
    max_movies: int,
    max_tags_per_movie: int,
) -> Tuple[List[Dict[str, object]], Dict[str, float], Dict[str, str]]:
    log(f"Processing flattened dataset {csv_path}")
    movies: Dict[str, Dict[str, object]] = {}
    global_scores: Dict[str, float] = defaultdict(float)

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            movie_id = str(
                row.get("movie_id")
                or row.get("movieId")
                or row.get("movieid")
            )
            tag = row.get("tag") or row.get("tag_name")
            title = row.get("title") or row.get("movie_title")
            relevance_raw = row.get("relevance") or row.get("score")
            if not movie_id or not tag or not relevance_raw:
                continue
            try:
                relevance = float(relevance_raw)
            except ValueError:
                continue
            if relevance < threshold:
                continue
            if movie_id not in movies and len(movies) >= max_movies:
                continue
            movie_entry = movies.setdefault(
                movie_id,
                {
                    "movie_id": movie_id,
                    "title": title or f"Movie {movie_id}",
                    "tags": [],
                },
            )
            movie_entry["tags"].append({"tag": tag, "relevance": relevance})
            global_scores[tag] += relevance

    documents: List[Dict[str, object]] = []
    for entry in movies.values():
        tags = sorted(
            entry["tags"],
            key=lambda item: item["relevance"],
            reverse=True,
        )[:max_tags_per_movie]
        if tags:
            documents.append(
                {
                    "movie_id": entry["movie_id"],
                    "title": entry["title"],
                    "tags": tags,
                }
            )
    return documents, dict(global_scores), {"source_flat": str(csv_path)}


def build_from_scores(
    scores_path: Path,
    tag_path: Optional[Path],
    movie_path: Optional[Path],
    threshold: float,
    max_movies: int,
    max_tags_per_movie: int,
) -> Tuple[List[Dict[str, object]], Dict[str, float], Dict[str, str]]:
    tag_map = load_tag_map(tag_path)
    title_map = load_movie_titles(movie_path)
    log(f"Processing genome scores from {scores_path}")

    movies: Dict[str, Dict[str, object]] = {}
    global_scores: Dict[str, float] = defaultdict(float)
    if isinstance(scores_path, tuple):
        file_path, columns = scores_path
        df = pd.read_csv(file_path, sep="\t", names=columns, engine="python")
        iterator = df.itertuples(index=False)
    else:
        with scores_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            iterator = reader

    for row in iterator:
        if isinstance(row, tuple):
            movie_id_val, tag_id_val, relevance_raw = row
        else:
            movie_id_val = row.get("movieId") or row.get("movie_id")
            tag_id_val = row.get("tagId") or row.get("tag_id")
            relevance_raw = row.get("relevance") or row.get("score")
        if not movie_id_val or not tag_id_val or not relevance_raw:
            continue
        movie_id = str(movie_id_val)
        try:
            relevance = float(relevance_raw)
        except ValueError:
            continue
        if relevance < threshold:
            continue
        if movie_id not in movies and len(movies) >= max_movies:
            continue
        tag_name = tag_map.get(str(tag_id_val), str(tag_id_val))
        entry = movies.setdefault(
            movie_id,
            {
                "movie_id": movie_id,
                "title": title_map.get(movie_id, f"Movie {movie_id}"),
                "tags": [],
            },
        )
        entry["tags"].append({"tag": tag_name, "relevance": relevance})
        global_scores[tag_name] += relevance

    documents: List[Dict[str, object]] = []
    for entry in movies.values():
        tags = sorted(
            entry["tags"],
            key=lambda item: item["relevance"],
            reverse=True,
        )[:max_tags_per_movie]
        if tags:
            documents.append(
                {
                    "movie_id": entry["movie_id"],
                    "title": entry["title"],
                    "tags": tags,
                }
            )

    context = {
        "scores_file": str(scores_path),
    }
    if tag_path:
        context["tags_file"] = str(tag_path)
    if movie_path:
        context["movies_file"] = str(movie_path)
    return documents, dict(global_scores), context


def derive_sample_query(global_scores: Dict[str, float]) -> Dict[str, object]:
    ordered_tags = sorted(
        global_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    top_tags = [tag for tag, _ in ordered_tags[:4]]
    description = (
        "Auto-generated query using the most frequent high-relevance tags."
        if top_tags
        else "Fallback query; no tags crossed the relevance threshold."
    )
    return {
        "name": "auto_tag_query",
        "description": description,
        "tags": top_tags or ["space travel", "action", "romance"],
    }


def write_jsonl(documents: List[Dict[str, object]], dest: Path) -> None:
    with dest.open("w", encoding="utf-8") as handle:
        for doc in documents:
            json.dump(doc, handle)
            handle.write("\n")
    log(f"Wrote {len(documents)} documents → {dest}")


def write_summary(documents: List[Dict[str, object]], dest: Path) -> None:
    summary = {
        "movies": len(documents),
        "tags": sum(len(doc["tags"]) for doc in documents),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    dest.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log(f"Wrote summary → {dest}")


def write_query(query: Dict[str, object], dest: Path) -> None:
    dest.write_text(json.dumps(query, indent=2), encoding="utf-8")
    log(f"Wrote sample query → {dest}")


def write_lineage(
    raw_dir: Path,
    dataset_path: Path,
    summary_path: Path,
    query_path: Path,
    dest: Path,
    threshold: float,
    max_movies: int,
    max_tags_per_movie: int,
    context: Dict[str, str],
) -> None:
    payload = {
        "raw_directory": str(raw_dir),
        "processed_dataset": str(dataset_path),
        "summary": str(summary_path),
        "query_file": str(query_path),
        "threshold": threshold,
        "max_movies": max_movies,
        "max_tags_per_movie": max_tags_per_movie,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_context": context,
    }
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log(f"Wrote lineage metadata → {dest}")


def build_documents(
    raw_dir: Path,
    threshold: float,
    max_movies: int,
    max_tags_per_movie: int,
) -> Tuple[List[Dict[str, object]], Dict[str, float], Dict[str, str]]:
    categorized = collect_sources(raw_dir)
    if categorized.get("flat"):
        return load_flat_dataset(
            categorized["flat"][0],
            threshold,
            max_movies,
            max_tags_per_movie,
        )
    scores_files = categorized.get("scores") or categorized.get("scores_dat")
    if not scores_files:
        raise FileNotFoundError(
            f"Could not find a compatible dataset under {raw_dir}. "
            "Expected a flattened CSV or genome-scores.csv."
        )
    tag_file = categorized.get("tags", [None])[0] or categorized.get("tags_dat", [None])[0]
    movie_file = categorized.get("movies", [None])[0] or categorized.get("movies_dat", [None])[0]
    return build_from_scores(
        scores_files[0],
        tag_file,
        movie_file,
        threshold,
        max_movies,
        max_tags_per_movie,
    )


def main() -> None:
    raw_dir = Path(os.getenv("RAW_DATA_DIR", "/data/raw")).resolve()
    processed_dir = Path(os.getenv("PROCESSED_DATA_DIR", "/data/processed")).resolve()
    query_dir = Path(os.getenv("QUERY_DIR", "/data/queries")).resolve()
    artifacts_dir = Path(os.getenv("ARTIFACT_DIR", "/data/artifacts")).resolve()

    bucket = os.getenv("GCS_BUCKET")
    prefix = os.getenv("GCS_PREFIX", "datasets/tag_genome")
    threshold = float(os.getenv("TAG_RELEVANCE_THRESHOLD", "0.75"))
    max_movies = int(os.getenv("MAX_MOVIES", "500"))
    max_tags_per_movie = int(os.getenv("MAX_TAGS_PER_MOVIE", "25"))

    ensure_dirs([raw_dir, processed_dir, query_dir, artifacts_dir])
    ensure_raw_data(raw_dir, bucket, prefix)
    inflate_archives(raw_dir)

    documents, global_scores, context = build_documents(
        raw_dir,
        threshold,
        max_movies,
        max_tags_per_movie,
    )
    if not documents:
        raise RuntimeError(
            "No documents generated from the raw dataset. "
            "Adjust thresholds or verify the source files."
        )

    dataset_path = processed_dir / "movies.jsonl"
    summary_path = processed_dir / "summary.json"
    query_path = query_dir / "sample_query.json"
    lineage_path = artifacts_dir / "lineage.json"

    write_jsonl(documents, dataset_path)
    write_summary(documents, summary_path)
    query_payload = derive_sample_query(global_scores)
    write_query(query_payload, query_path)
    write_lineage(
        raw_dir,
        dataset_path,
        summary_path,
        query_path,
        lineage_path,
        threshold,
        max_movies,
        max_tags_per_movie,
        context,
    )
    log("Data preprocessing complete ✅")


if __name__ == "__main__":
    main()
