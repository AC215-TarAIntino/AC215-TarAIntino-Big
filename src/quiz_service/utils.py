import numpy as np
from pathlib import Path
from .config import get_collection, PRIOR_MEAN_PATH, PRIOR_COV_PATH

def _compute_and_save_prior_if_needed():
    mean_p = Path(PRIOR_MEAN_PATH)
    cov_p  = Path(PRIOR_COV_PATH)
    if mean_p.exists() and cov_p.exists():
        return

    col = get_collection()
    sample = col.peek(20000)

    embs = sample.get("embeddings", None)
    # Handle None or 0-length explicitly to avoid NumPy truthiness
    if embs is None or len(embs) == 0:
        raise RuntimeError("No embeddings in Chroma; run the downloader/ingester first.")

    X = np.asarray(embs, dtype=np.float64)
    if X.ndim != 2:
        raise RuntimeError(f"Expected 2D embeddings, got shape {X.shape}")

    mu  = X.mean(axis=0)
    Cov = np.cov(X, rowvar=False)
    Cov = Cov + 1e-3 * np.eye(Cov.shape[0], dtype=np.float64)

    np.save(mean_p, mu)
    np.save(cov_p, Cov)

def topN_from_matrix(theta_hat: np.ndarray, X: np.ndarray, ids, metas, N=10):
    t = theta_hat / (np.linalg.norm(theta_hat) + 1e-12)
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
    sims = Xn @ t
    order = np.argsort(-sims)[:N]
    out = []
    for k in order:
        mid = str(ids[k])
        title = (metas[k] or {}).get("title") if metas and k < len(metas) else None
        out.append({"movie_id": mid, "title": title or f"Movie {mid}", "score": float(sims[k])})
    return out