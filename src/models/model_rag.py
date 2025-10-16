import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


def log(message: str) -> None:
    print(f"[MODEL {time.strftime('%Y-%m-%d %H:%M:%S')}] {message}", flush=True)


@dataclass
class MovieDocument:
    movie_id: str
    title: str
    tags: Dict[str, float]

    def score(self, query_tags: Sequence[str]) -> Dict[str, object]:
        ordered_tags = list(dict.fromkeys(query_tags))
        total = sum(self.tags.get(tag, 0.0) for tag in ordered_tags)
        matched = [
            {"tag": tag, "relevance": self.tags[tag]}
            for tag in ordered_tags
            if tag in self.tags
        ]
        coverage = round(len(matched) / len(ordered_tags), 2) if ordered_tags else 0.0
        return {
            "movie_id": self.movie_id,
            "title": self.title,
            "score": round(total, 4),
            "matched_tags": matched,
            "top_tags": sorted(
                [
                    {"tag": tag, "relevance": rel}
                    for tag, rel in self.tags.items()
                ],
                key=lambda item: item["relevance"],
                reverse=True,
            )[:5],
            "coverage": coverage,
        }


def load_documents(dataset_path: Path) -> List[MovieDocument]:
    documents: List[MovieDocument] = []
    with dataset_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line.strip())
            tags = {entry["tag"]: float(entry["relevance"]) for entry in payload["tags"]}
            documents.append(
                MovieDocument(
                    movie_id=str(payload["movie_id"]),
                    title=payload["title"],
                    tags=tags,
                )
            )
    log(f"Loaded {len(documents)} documents from {dataset_path}")
    return documents


def load_query(query_path: Path) -> Dict[str, object]:
    payload = json.loads(query_path.read_text(encoding="utf-8"))
    log(f"Loaded query '{payload.get('name', 'unnamed')}' from {query_path}")
    return payload


def rank_movies(documents: Iterable[MovieDocument], query_tags: Sequence[str]) -> List[Dict[str, object]]:
    ranked = [doc.score(query_tags) for doc in documents]
    return sorted(ranked, key=lambda item: item["score"], reverse=True)


def write_recommendations(recommendations: List[Dict[str, object]], dest: Path, limit: int = 3) -> None:
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "recommendations": recommendations[:limit],
    }
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log(f"Wrote recommendations → {dest}")


def write_inference_log(
    dataset_path: Path, query_payload: Dict[str, object], recommendations_path: Path, dest: Path
) -> None:
    log_payload = {
        "dataset": str(dataset_path),
        "query": query_payload,
        "recommendations": str(recommendations_path),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    dest.write_text(json.dumps(log_payload, indent=2), encoding="utf-8")
    log(f"Wrote inference log → {dest}")


def main() -> None:
    processed_dir = Path(os.getenv("PROCESSED_DATA_DIR", "/data/processed"))
    query_dir = Path(os.getenv("QUERY_DIR", "/data/queries"))
    output_dir = Path(os.getenv("OUTPUT_DIR", "/outputs"))
    artifacts_dir = Path(os.getenv("ARTIFACT_DIR", "/outputs/artifacts"))

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = processed_dir / "movies.jsonl"
    query_path = query_dir / "sample_query.json"
    recommendations_path = output_dir / "recommendations.json"
    log_path = artifacts_dir / "inference_log.json"

    documents = load_documents(dataset_path)
    query_payload = load_query(query_path)
    recommendations = rank_movies(documents, query_payload.get("tags", []))

    write_recommendations(recommendations, recommendations_path)
    write_inference_log(dataset_path, query_payload, recommendations_path, log_path)

    if recommendations:
        top_titles = ", ".join(rec["title"] for rec in recommendations[:3])
        log(f"Top matches: {top_titles}")
    else:
        log("No recommendations found for the supplied query.")
    log("Model inference complete ✅")


if __name__ == "__main__":
    main()
