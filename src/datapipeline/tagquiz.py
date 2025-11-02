import os
import json
import numpy as np
from typing import List, Tuple, Dict
import chromadb
from pathlib import Path

###############################################################################
# CONFIG: human-friendly quiz tags (tag_id from tags.dat, nice label for UI)
###############################################################################

QUIZ_TAGS = [
    (416, "funny"),
    (284, "dark"),
    (862, "romance"),
    (1084, "violent"),
    (496, "heartwarming"),
    (311, "disturbing"),
    (347, "emotional"),
    (1023, "thought-provoking"),
    (886, "sci-fi"),
    (267, "crime"),
    (376, "fantasy"),
    (18,  "action"),
    (521, "horror"),
    (229, "comedy"),
    (322, "drama"),
    (688, "mystery"),
]

PRIOR_MEAN_PATH = "/app/prior_mean.npy"
PRIOR_COV_PATH  = "/app/prior_cov.npy"

###############################################################################
# Chroma helpers
###############################################################################

def get_chroma_client():
    host = os.getenv("CHROMA_SERVER_HOST")
    port = os.getenv("CHROMA_SERVER_PORT")
    if host and port:
        return chromadb.HttpClient(host=host, port=int(port))
    path = os.getenv("CHROMA_PATH", "./chroma_db")
    return chromadb.PersistentClient(path=path)

def get_collection(collection_name: str):
    client = get_chroma_client()
    return client.get_collection(collection_name)

###############################################################################
# Map raw tag_id -> column index in embeddings (from dataloader tag_index.json)
###############################################################################

def load_tagid_to_colindex(mapping_json_path: str) -> Dict[int, int]:
    with open(mapping_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tag_ids_sorted = data["tag_ids_sorted"]  # list[int]
    return {tid: j for j, tid in enumerate(tag_ids_sorted)}

###############################################################################
# Phase A helper (potentially expensive): build prior mean and cov
###############################################################################

def compute_and_save_prior(chroma_collection, save_mean=PRIOR_MEAN_PATH, save_cov=PRIOR_COV_PATH):
    """
    Pulls (up to) all movie embeddings from Chroma,
    computes empirical mean + covariance over tag space,
    regularizes covariance, and saves them.
    Only do this if the npy files don't already exist.
    """
    print("[prior] computing prior mean/cov from Chroma…")

    # heuristic upper bound well above 9734
    sample = chroma_collection.peek(20000)

    embs = sample.get("embeddings", None)
    ids  = sample.get("ids", None)
    if embs is None or len(embs) == 0:
        raise RuntimeError("Could not fetch embeddings from Chroma. Did you ingest data?")

    X = np.array(embs, dtype=np.float64)  # shape (N,D)
    N, D = X.shape
    print(f"[prior] Loaded {N} movie vectors, dim={D}")

    mu = np.mean(X, axis=0)               # (D,)
    Cov = np.cov(X, rowvar=False)         # (D,D)

    # Ridge for stability
    eps = 1e-3
    Cov_reg = Cov + eps * np.eye(D, dtype=np.float64)

    np.save(save_mean, mu)
    np.save(save_cov, Cov_reg)

    print(f"[prior] Saved {save_mean} and {save_cov}")
    return mu, Cov_reg

###############################################################################
# Our full 1128-D correlated preference model
###############################################################################

class FullCovarianceTasteModel:
    """
    Full Gaussian preference model in D dimensions (D ~1128 tags).

    State:
      theta_hat : (D,)   current belief of user's taste per tag
      Sigma     : (D,D)  current covariance
      sigma2    : scalar observation noise
      quiz_cols : (K,)   which dims correspond to our human-facing sliders
      quiz_texts: list[str] labels
      asked_mask: (K,)   which sliders we've already asked
    """

    def __init__(
        self,
        prior_mean: np.ndarray,       # (D,)
        prior_cov: np.ndarray,        # (D,D)
        tagid2col: Dict[int, int],    # tag_id -> column index in embedding space
        quiz_tags: List[Tuple[int, str]],
        sigma2: float = 0.05,
    ):
        assert prior_mean.ndim == 1
        assert prior_cov.ndim == 2
        D = prior_mean.shape[0]
        assert prior_cov.shape == (D, D), "prior_cov must be DxD"

        self.D = D
        self.theta_hat = prior_mean.astype(np.float64).copy()   # (D,)
        self.Sigma     = prior_cov.astype(np.float64).copy()    # (D,D)
        self.sigma2    = float(sigma2)

        # map quiz_tags → embedding dims
        quiz_cols = []
        quiz_texts = []
        for (tid, txt) in quiz_tags:
            if tid in tagid2col:
                quiz_cols.append(tagid2col[tid])
                quiz_texts.append(txt)

        if len(quiz_cols) == 0:
            raise ValueError("None of the QUIZ_TAGS matched tagid2col mapping.")
        self.quiz_cols  = np.array(quiz_cols, dtype=int)  # (K,)
        self.quiz_texts = list(quiz_texts)                # len K
        self.K          = len(self.quiz_cols)

        self.asked_mask = np.zeros(self.K, dtype=bool)

    def pick_next_quiz_tag(self) -> int:
        """
        Choose which quiz slider (index in [0..K-1]) to ask next.
        We pick the not-yet-asked one with largest current variance.
        """
        variances = np.array([self.Sigma[j, j] for j in self.quiz_cols], dtype=np.float64)
        variances[self.asked_mask] = -1e9  # force already-asked to bottom
        k_next = int(np.argmax(variances))
        return k_next

    def ask_question_text(self, k: int) -> str:
        label = self.quiz_texts[k]
        return f"On a scale from 1 to 10, how much do you want the movie to be '{label}'?"

    def update_with_answer(self, k: int, answer_1to10: float):
        """
        Kalman-style rank-1 update in the full D-dim space.
        Observation model: y = theta[j] + noise, noise ~ N(0, sigma2).
        """
        j = int(self.quiz_cols[k])  # global index in [0..D-1]

        # scale user's answer 1..10 -> [0,1]
        y = float(answer_1to10) / 10.0
        y = min(max(y, 0.0), 1.0)

        theta_j = self.theta_hat[j]
        v_jj    = self.Sigma[j, j]
        denom   = v_jj + self.sigma2  # scalar

        # Kalman gain vector (D,)
        k_vec = self.Sigma[:, j] / denom  # (D,)

        # mean update
        residual = (y - theta_j)
        self.theta_hat = self.theta_hat + k_vec * residual  # (D,)

        # covariance update: Σ <- Σ - k_vec * Σ[j,:]
        row_j = self.Sigma[j, :]  # (D,)
        self.Sigma = self.Sigma - np.outer(k_vec, row_j)

        # mark this slider as asked
        self.asked_mask[k] = True

        # keep Σ symmetric numerically
        self.Sigma = 0.5 * (self.Sigma + self.Sigma.T)

    def report_tag_status(self):
        """
        Returns two lists (for pretty CLI printout):
          top_prefs:    [(label, mean_at_that_tag), ...] sorted by descending mean
          top_uncert:   [(label, var_at_that_tag),  ...] sorted by descending var
        Only within our quiz tag subset.
        """
        means = np.array([self.theta_hat[j] for j in self.quiz_cols], dtype=np.float64)
        vars_ = np.array([self.Sigma[j, j]   for j in self.quiz_cols], dtype=np.float64)

        order_mean = np.argsort(-means)
        order_var  = np.argsort(-vars_)

        top_prefs = [(self.quiz_texts[i], float(means[i])) for i in order_mean]
        top_unc   = [(self.quiz_texts[i], float(vars_[i])) for i in order_var]

        return top_prefs, top_unc

    def recommend_topN_from_chroma(
        self,
        chroma_collection,
        N: int = 10,
        max_candidates: int = 300,
    ) -> List[Tuple[str, str, float]]:
        """
        1. Pull ~max_candidates movies from Chroma (ids, embeds, titles)
        2. Cosine similarity with current theta_hat (full D)
        3. Return ranked [(movie_id, title, sim), ...]
        """
        theta_norm = np.linalg.norm(self.theta_hat) + 1e-12
        t_hat = self.theta_hat / theta_norm  # (D,)

        sample = chroma_collection.peek(max_candidates)
        cand_ids   = sample.get("ids", [])
        cand_embs  = sample.get("embeddings", [])
        cand_metas = sample.get("metadatas", [])

        if cand_ids is None or cand_embs is None:
            raise RuntimeError("Chroma.peek() returned no ids/embeddings.")
        if len(cand_ids) == 0 or len(cand_embs) == 0:
            raise RuntimeError("No candidate movies from Chroma.peek().")

        X = np.array(cand_embs, dtype=np.float64)   # (M,D)
        X_norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
        X_hat = X / X_norms                          # (M,D)

        sims = X_hat @ t_hat                         # (M,)

        order = np.argsort(-sims)[:N]

        out = []
        for idx in order:
            mid = str(cand_ids[idx])
            title = f"Movie {mid}"
            if cand_metas and idx < len(cand_metas) and cand_metas[idx] is not None:
                maybe_title = cand_metas[idx].get("title")
                if maybe_title:
                    title = maybe_title
            out.append((mid, title, float(sims[idx])))

        return out

###############################################################################
# MAIN (Phase B quiz + fallback Phase A prior building if needed)
###############################################################################

if __name__ == "__main__":
    collection_name = os.getenv("CHROMA_COLLECTION", "movie_tag_relevance_cos")
    mapping_json_path = f"/app/logs/{collection_name}__tag_index.json"

    # --- connect to Chroma and get dim
    col = get_collection(collection_name)
    peek_one = col.peek(1)
    D = len(peek_one["embeddings"][0])
    print(f"[init] embedding dim from Chroma = {D}")

    # --- ensure we have prior files; if not, build and save
    mean_file = Path(PRIOR_MEAN_PATH)
    cov_file  = Path(PRIOR_COV_PATH)

    if mean_file.exists() and cov_file.exists():
        print("[init] loading cached prior mean/cov …")
        prior_mean = np.load(PRIOR_MEAN_PATH)
        prior_cov  = np.load(PRIOR_COV_PATH)
    else:
        print("[init] prior *.npy not found, computing now …")
        prior_mean, prior_cov = compute_and_save_prior(col)

    # sanity check shapes
    if prior_mean.shape[0] != D or prior_cov.shape != (D, D):
        raise RuntimeError(
            f"Prior shape mismatch: mean {prior_mean.shape}, cov {prior_cov.shape}, expected D={D}"
        )

    # --- load tag_id -> col index mapping for quiz tag IDs
    print("[init] loading tagid2col mapping …")
    tagid2col = load_tagid_to_colindex(mapping_json_path)

    # --- init full covariance model
    model = FullCovarianceTasteModel(
        prior_mean=prior_mean,
        prior_cov=prior_cov,
        tagid2col=tagid2col,
        quiz_tags=QUIZ_TAGS,
        sigma2=0.05,
    )

    print(f"[init] quiz has K={model.K} sliders mapped into {model.D}-dim taste space.")
    print("[init] we'll adaptively ask the most uncertain sliders first.\n")

    # --- interactive loop
    num_q = 5
    for step in range(num_q):
        k = model.pick_next_quiz_tag()
        question = model.ask_question_text(k)

        print(f"Question {step+1}: {question}")
        raw = input("Your answer (1-10): ").strip()
        try:
            ans = float(raw)
        except:
            ans = 5.0

        model.update_with_answer(k, ans)

        # progress report for this slider
        j_global = model.quiz_cols[k]
        new_mean = model.theta_hat[j_global]
        new_var  = model.Sigma[j_global, j_global]
        print(f" -> '{model.quiz_texts[k]}' now mean≈{new_mean:.3f}, var≈{new_var:.4f}\n")

    # --- summary: what you like / what we're unsure about
    top_prefs, top_unc = model.report_tag_status()

    print("[summary] strongest expressed prefs (quiz tags):")
    for label, m in top_prefs[:8]:
        print(f"  {label:20s} pref≈{m:.3f}")

    print("\n[summary] most uncertain tags (quiz tags):")
    for label, v in top_unc[:8]:
        print(f"  {label:20s} var≈{v:.4f}")

    # --- final recs
    print("\n[recs] computing movie recommendations …")
    recs = model.recommend_topN_from_chroma(
        chroma_collection=col,
        N=10,
        max_candidates=300,
    )

    print("\nYour top-10 right now:")
    for mid, title, score in recs:
        print(f"  {title} [{mid}]: {score:.4f}")

