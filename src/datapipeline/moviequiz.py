import os
import numpy as np
from typing import Tuple, List, Optional
import chromadb

###############################################################################
# Utilities to talk to Chroma (same pattern as in dataloader.py / similarity.py)
###############################################################################

def get_chroma_client():
    host = os.getenv("CHROMA_SERVER_HOST")
    port = os.getenv("CHROMA_SERVER_PORT")
    if host and port:
        return chromadb.HttpClient(host=host, port=int(port))
    # fallback: local persistent client
    path = os.getenv("CHROMA_PATH", "./chroma_db")
    return chromadb.PersistentClient(path=path)


def get_collection(collection_name: str):
    client = get_chroma_client()
    return client.get_collection(collection_name)


def get_movie_embedding(collection, movie_id: str) -> np.ndarray:
    """
    Fetch x_movie \in R^T for a given movie_id from Chroma.
    """
    got = collection.get(ids=[str(movie_id)], include=["embeddings"])
    embs = got.get("embeddings")
    if embs is None or len(embs) == 0:
        raise ValueError(f"No embedding found for movie {movie_id}")
    vec = np.array(embs[0], dtype=np.float64)
    return vec


def get_many_movie_embeddings(collection, movie_ids: List[str]) -> np.ndarray:
    """
    Returns matrix X of shape (len(movie_ids), dim).
    """
    got = collection.get(ids=[str(m) for m in movie_ids], include=["embeddings"])
    embs = got.get("embeddings")
    if embs is None or len(embs) != len(movie_ids):
        raise ValueError("Mismatch when fetching multiple embeddings.")
    X = np.array(embs, dtype=np.float64)
    return X


def peek_collection_info(collection) -> Tuple[List[str], int]:
    """
    Peek 1 item from the collection, return (ids, dim)
    """
    sample = collection.peek(1)
    ids = sample.get("ids", [])
    embs = sample.get("embeddings", [])
    if embs is None or len(embs) == 0:
        raise ValueError("Collection appears empty; cannot infer dimension.")
    dim = len(embs[0])
    return ids, dim


###############################################################################
# Core Taste Model Class
###############################################################################

class TasteModel:
    """
    Maintains:
    - theta            : current estimate of user's taste vector in tag space (R^T)
    - H                : current precision / Hessian approx (T x T)
    - g                : accumulated gradient term (T,)
    - movie_ids_cache  : list[str] of movies we consider for questioning/recs
    - X_cache          : np.ndarray shape (num_movies_considered, T)
                         aligned with movie_ids_cache
    """

    def __init__(
        self,
        collection_name: str = "movie_tag_relevance_cos",
        lambda_reg: float = 1.0,
        candidate_movie_ids: Optional[List[str]] = None,
        max_candidates: int = 200,
    ):
        """
        lambda_reg: prior precision λ.
            Prior: theta ~ N(0, (1/λ) I).
            So H_0 = λ I, g_0 = 0, theta_0 = 0.

        candidate_movie_ids:
            If None, we'll grab up to max_candidates movies from collection.peek().
            Otherwise we fetch those specific movie IDs (in that order, truncated).
        """
        self.collection_name = collection_name
        self.collection = get_collection(collection_name)

        # pick candidate set of movies
        if candidate_movie_ids is None:
            # chroma.peek(k) returns at most k items
            peek_k = max_candidates
            sample = self.collection.peek(peek_k)
            ids = sample.get("ids", [])
            embs = sample.get("embeddings", [])
            metas = sample.get("metadatas", [])

            # FIX: avoid "truth value of array is ambiguous"
            if ids is None or embs is None or len(ids) == 0 or len(embs) == 0:
                raise ValueError("Collection is empty or peek failed.")

            # cache
            self.movie_ids_cache = [str(i) for i in ids[:max_candidates]]
            X_list = embs[:max_candidates]
            self.X_cache = np.array(X_list, dtype=np.float64)

            titles_list = []
            for meta in metas[:max_candidates]:
                if isinstance(meta, dict):
                    titles_list.append(meta.get("title", f"Movie {meta.get('movieId', '???')}"))
                else:
                    titles_list.append("Unknown Title")
            self.titles_cache = titles_list

        else:
            # explicit subset from caller
            self.movie_ids_cache = [str(m) for m in candidate_movie_ids[:max_candidates]]
            self.X_cache = get_many_movie_embeddings(self.collection, self.movie_ids_cache)

        # dimension = number of tags per movie vector
        self.dim = self.X_cache.shape[1]

        # Initialize posterior / MAP state
        # theta starts at 0
        self.theta = np.zeros(self.dim, dtype=np.float64)

        # H starts as λ I  (precision matrix)
        self.H = lambda_reg * np.eye(self.dim, dtype=np.float64)

        # g starts as λ(θ-μ0), but μ0=0, θ=0 => 0
        self.g = np.zeros(self.dim, dtype=np.float64)

        # we'll cache Sigma = H^{-1} only when needed
        self._Sigma_cache = None
        self._Sigma_dirty = True

    ###########################################################################
    # Internal helpers
    ###########################################################################

    def _invalidate_Sigma(self):
        self._Sigma_dirty = True
        self._Sigma_cache = None

    def get_precision(self) -> np.ndarray:
        return self.H

    def get_covariance(self) -> np.ndarray:
        """
        Sigma = H^{-1}.
        This is O(T^3), so don't call each frame unnecessarily.
        """
        if self._Sigma_dirty or self._Sigma_cache is None:
            self._Sigma_cache = np.linalg.inv(self.H)
            self._Sigma_dirty = False
        return self._Sigma_cache

    def _phi(self, idx_i: int, idx_j: int) -> np.ndarray:
        """
        phi = x_i - x_j for two indices into self.movie_ids_cache.
        """
        return self.X_cache[idx_i] - self.X_cache[idx_j]

    def _pair_margin_prob(self, phi: np.ndarray) -> Tuple[float, float, float]:
        """
        Given phi, compute margin m = theta^T phi,
        p = sigmoid(m), and w = p(1-p).
        """
        m = float(self.theta @ phi)
        p = 1.0 / (1.0 + np.exp(-m))
        w = p * (1.0 - p)
        return m, p, w

    ###########################################################################
    # Public API
    ###########################################################################

    def get_candidate_movie_ids(self) -> List[str]:
        return list(self.movie_ids_cache)

    def update_with_answer(self, idx_i: int, idx_j: int, picked_i: bool):
        """
        Update theta, H, g after the user answers:
        - idx_i, idx_j: indices in self.movie_ids_cache
        - picked_i=True  means user preferred movie_i
        - picked_i=False means user preferred movie_j
        """
        phi = self._phi(idx_i, idx_j)  # shape (dim,)
        m, p, w = self._pair_margin_prob(phi)
        y = 1.0 if picked_i else 0.0

        # rank-1 precision update: H += w * phi phi^T
        outer = np.outer(phi, phi)     # (dim,dim)
        self.H += w * outer

        # gradient accumulator update: g += (p - y) * phi
        self.g += (p - y) * phi

        # Newton step:
        # Solve H * delta = g  => delta = H^{-1} g
        delta = np.linalg.solve(self.H, self.g)
        self.theta = self.theta - delta

        # mark Sigma dirty
        self._invalidate_Sigma()

    def score_pair_information(self, idx_i: int, idx_j: int, Sigma: Optional[np.ndarray] = None) -> float:
        """
        Acquisition score U(i,j) = w * phi^T Sigma phi.
        High U => good next question.
        """
        phi = self._phi(idx_i, idx_j)
        _, _, w = self._pair_margin_prob(phi)

        if Sigma is None:
            Sigma = self.get_covariance()

        u = float(phi @ (Sigma @ phi))  # directional variance
        U = w * u
        return U

    def choose_next_pair(self, max_pairs: int = 2000) -> Tuple[int, int, float]:
        """
        Choose the most informative pair from cached candidates.

        We either consider all pairs (if small) or randomly sample up to max_pairs.
        Returns (idx_i, idx_j, U_value).
        """
        n_movies = len(self.movie_ids_cache)
        rng = np.random.default_rng()
        num_possible = n_movies * (n_movies - 1) // 2

        if num_possible <= max_pairs:
            pairs = [(i, j) for i in range(n_movies) for j in range(i + 1, n_movies)]
        else:
            pairs = set()
            while len(pairs) < max_pairs:
                i = rng.integers(0, n_movies)
                j = rng.integers(0, n_movies)
                if i == j:
                    continue
                a, b = (i, j) if i < j else (j, i)
                pairs.add((a, b))
            pairs = list(pairs)

        Sigma = self.get_covariance()

        bestU = -1.0
        best_pair = (0, 1)
        for (i, j) in pairs:
            U_val = self.score_pair_information(i, j, Sigma=Sigma)
            if U_val > bestU:
                bestU = U_val
                best_pair = (i, j)

        return best_pair[0], best_pair[1], bestU

    def pick_initial_pair_max_distance(
        self,
        subset_size: int = 1000,
        rng: Optional[np.random.Generator] = None,
    ) -> Tuple[int, int, float]:
        """
        Heuristic for the very first question:
        - Sample up to `subset_size` movies from the cache.
        - Among JUST that sample, find the pair with the largest squared distance.
        This avoids O(n^2) over all ~9000 movies.

        Returns (idx_i, idx_j, best_d2) where idx_i/idx_j are indices back into
        *the FULL self.movie_ids_cache*, not 0..subset_size-1.
        """

        n_movies = len(self.movie_ids_cache)
        if rng is None:
            rng = np.random.default_rng()

        if n_movies <= subset_size:
            # small case: just brute force them all
            candidate_indices = np.arange(n_movies)
        else:
            # big case: random subset without replacement
            candidate_indices = rng.choice(n_movies, size=subset_size, replace=False)

        # pull the subset of embeddings
        X_sub = self.X_cache[candidate_indices]  # shape (subset_size, dim)

        best_d2 = -1.0
        best_pair_local = (0, 1)

        # brute force just within the subset
        m = len(candidate_indices)
        for a in range(m):
            xa = X_sub[a]
            # we only compare to b > a to avoid duplicates
            for b in range(a + 1, m):
                d2 = float(np.sum((xa - X_sub[b]) ** 2))
                if d2 > best_d2:
                    best_d2 = d2
                    best_pair_local = (a, b)

        # map back to global indices in self.movie_ids_cache / self.X_cache
        global_i = int(candidate_indices[best_pair_local[0]])
        global_j = int(candidate_indices[best_pair_local[1]])

        return global_i, global_j, best_d2


    def recommend_topN(self, N: int = 10) -> List[Tuple[str, str, float]]:
        """
        Returns list of (movie_id, title, cosine_sim_score)
        """
        theta_norm = np.linalg.norm(self.theta) + 1e-12
        t_hat = self.theta / theta_norm

        X_norms = np.linalg.norm(self.X_cache, axis=1, keepdims=True) + 1e-12
        X_hat = self.X_cache / X_norms
        sims = X_hat @ t_hat  # (num_movies,)

        order = np.argsort(-sims)[:N]
        out = []
        for idx in order:
            out.append((self.movie_ids_cache[idx],
                        self.titles_cache[idx],
                        float(sims[idx])))
        return out



###############################################################################
# Interactive CLI for testing inside the container
###############################################################################

if __name__ == "__main__":
    # 1. init model
    collection_name = os.getenv("CHROMA_COLLECTION", "movie_tag_relevance_cos")
    model = TasteModel(
        collection_name=collection_name,
        lambda_reg=1.0,
        max_candidates=9000,   # you can bump this up if performance is fine
    )

    print("[info] Loaded", len(model.movie_ids_cache), "candidate movies")
    print("[info] Embedding dim =", model.dim)

    # 2. ask ~10 questions interactively
    for step in range(10):
        if step == 0:
            i, j, _ = model.pick_initial_pair_max_distance()
        else:
            i, j, _ = model.choose_next_pair(max_pairs=1000)

        movie_i_id = model.movie_ids_cache[i]
        movie_j_id = model.movie_ids_cache[j]
        movie_i_title = model.titles_cache[i]
        movie_j_title = model.titles_cache[j]

        print(f"\nQuestion {step+1}: which do you prefer?")
        print(f"  (0) {movie_i_title} [{movie_i_id}]")
        print(f"  (1) {movie_j_title} [{movie_j_id}]")

        ans = input("Your choice [0/1]: ").strip()
        picked_i = (ans == "0")

        model.update_with_answer(i, j, picked_i=picked_i)
        print(f" -> updated ||theta|| = {np.linalg.norm(model.theta):.4f}")

    # 3. show recs
    recs = model.recommend_topN(N=10)
    print("\nYour top-10 right now:")
    for mid, title, score in recs:
        print(f"  {title} [{mid}]: {score:.4f}")

# import os
# import numpy as np
# from typing import Tuple, List, Optional
# import chromadb
# import pathlib

# ###############################################################################
# # Utilities to talk to Chroma
# ###############################################################################

# def get_chroma_client():
#     host = os.getenv("CHROMA_SERVER_HOST")
#     port = os.getenv("CHROMA_SERVER_PORT")
#     if host and port:
#         return chromadb.HttpClient(host=host, port=int(port))
#     # fallback: local persistent client
#     path = os.getenv("CHROMA_PATH", "./chroma_db")
#     return chromadb.PersistentClient(path=path)

# def get_collection(collection_name: str):
#     client = get_chroma_client()
#     return client.get_collection(collection_name)

# def safe_chroma_peek(collection, k: int):
#     """
#     Wraps Chroma .peek(k) and normalizes output so we never trigger
#     'truth value of array is ambiguous'.
#     Returns (ids:List[str], embeds:np.ndarray, metas:List[dict])
#     """
#     sample = collection.peek(k)
#     cand_ids = sample.get("ids", [])
#     cand_embs = sample.get("embeddings", [])
#     cand_metas = sample.get("metadatas", [])

#     if cand_ids is None or cand_embs is None:
#         raise ValueError("Chroma.peek() returned no ids/embeddings.")
#     if len(cand_ids) == 0 or len(cand_embs) == 0:
#         raise ValueError("No candidate movies available from Chroma.peek().")

#     X = np.array(cand_embs, dtype=np.float64)  # shape (M, D)

#     # Normalize metas list
#     norm_metas = []
#     for m in cand_metas[:len(cand_ids)]:
#         norm_metas.append(m if isinstance(m, dict) else {})

#     # string-ify ids
#     norm_ids = [str(mid) for mid in cand_ids]

#     return norm_ids, X, norm_metas

# def build_titles_cache(metas: List[dict], fallback_ids: List[str]) -> List[str]:
#     out = []
#     for meta, mid in zip(metas, fallback_ids):
#         title_str = None
#         if isinstance(meta, dict):
#             # 1. try explicit title
#             if "title" in meta and meta["title"]:
#                 title_str = meta["title"]
#             # 2. fallback to "Movie <movieId>"
#             elif "movieId" in meta:
#                 title_str = f"Movie {meta['movieId']}"
#         # 3. final fallback
#         if title_str is None:
#             title_str = f"Movie {mid}"
#         out.append(title_str)
#     return out

# ###############################################################################
# # Prior estimation across the WHOLE movie space
# ###############################################################################

# def compute_or_load_global_prior(
#     collection,
#     prior_mean_path: str = "/app/prior_mean.npy",
#     prior_cov_path: str  = "/app/prior_cov.npy",
#     ridge: float = 1e-3,
# ) -> Tuple[np.ndarray, np.ndarray]:
#     """
#     We try to load prior mean/cov from disk.
#     If not found, we:
#       - pull ALL movies (in batches, but here we'll cheat and assume .get() or .peek() large enough;
#         if not, you can extend with batching),
#       - compute empirical mean and covariance,
#       - add tiny ridge to cov for numerical stability,
#       - save them as .npy.
#     Returns (mu0, Sigma0).
#     """

#     pm_path = pathlib.Path(prior_mean_path)
#     pc_path = pathlib.Path(prior_cov_path)

#     if pm_path.exists() and pc_path.exists():
#         mu0 = np.load(pm_path)
#         Sigma0 = np.load(pc_path)
#         return mu0, Sigma0

#     # ---- Fallback compute path ----
#     # Best effort: try to grab *all* vectors from Chroma by IDs in chunks.
#     # We don't yet have a quick "list all" in your code, so we’ll exploit peek()
#     # with something big, like 20000, because you have ~9734 movies.
#     # If you want truly robust batching by ID later, you can add it.

#     print("[prior] computing prior mean/cov from Chroma…", flush=True)
#     all_ids, all_X, _ = safe_chroma_peek(collection, k=20000)
#     # all_X shape = (N_movies, D)

#     mu0 = np.mean(all_X, axis=0)  # (D,)
#     # covariance (unbiased-ish). We'll do rowvar=False => columns are vars.
#     Sigma0 = np.cov(all_X, rowvar=False)  # (D,D)

#     # numerical stability: add ridge on diagonal
#     Sigma0 = Sigma0 + ridge * np.eye(Sigma0.shape[0], dtype=np.float64)

#     # save for reuse
#     np.save(pm_path, mu0)
#     np.save(pc_path, Sigma0)

#     return mu0, Sigma0


# ###############################################################################
# # MoviePairBayesModel
# #   - theta_hat:   (D,) current belief about user's taste
# #   - Sigma:       (D,D) covariance of that belief
# #   - X_cache:     (M,D) movie tag embeddings for candidate movies
# #   - titles_cache:(M,)  titles aligned with rows of X_cache
# #   - movie_ids_cache: (M,) ids aligned with rows
# #
# # Update rule (linear-Gaussian approx for pairwise preference):
# #   Observation: y = phi^T theta + noise, noise ~ N(0, sigma2)
# #   where:
# #      phi = x_i - x_j  (movie i vs j)
# #      y   = 1 if user prefers i, 0 if user prefers j
# #
# # Kalman update:
# #   pred = phi^T theta_hat
# #   S    = phi^T Sigma phi + sigma2
# #   K    = Sigma phi / S        (shape D)
# #   theta_hat <- theta_hat + K * (y - pred)
# #   Sigma     <- Sigma - K (phi^T Sigma)
# #
# ###############################################################################

# class MoviePairBayesModel:
#     def __init__(
#         self,
#         collection_name: str = "movie_tag_relevance_cos",
#         sigma2_obs: float = 0.05,   # noise on user's comparison answers
#         max_candidates: int = 500,  # how many movies we consider at once
#         prior_mean_path: str = "/app/prior_mean.npy",
#         prior_cov_path: str  = "/app/prior_cov.npy",
#     ):
#         self.collection_name = collection_name
#         self.collection = get_collection(collection_name)

#         # 1. grab candidate movies (ids, embeddings, titles)
#         movie_ids, X_mat, metas = safe_chroma_peek(self.collection, k=max_candidates)
#         self.movie_ids_cache = movie_ids                        # list[str], len M
#         self.X_cache = X_mat                                    # (M,D)
#         self.titles_cache = build_titles_cache(metas, movie_ids)# list[str], len M

#         self.dim = self.X_cache.shape[1]
#         self.M   = self.X_cache.shape[0]

#         # 2. load or compute global prior
#         print("[init] embedding dim from Chroma =", self.dim, flush=True)
#         mu0, Sigma0 = compute_or_load_global_prior(
#             self.collection,
#             prior_mean_path=prior_mean_path,
#             prior_cov_path=prior_cov_path,
#         )

#         # Sanity: shapes
#         if mu0.shape[0] != self.dim:
#             raise ValueError(f"prior mean dim {mu0.shape[0]} != movie dim {self.dim}")
#         if Sigma0.shape != (self.dim, self.dim):
#             raise ValueError(f"prior cov shape {Sigma0.shape} != {(self.dim,self.dim)}")

#         self.theta_hat = mu0.copy()      # start from population average tastes
#         self.Sigma     = Sigma0.copy()   # uncertainty over that taste
#         self.sigma2    = float(sigma2_obs)

#         # to avoid repeating same pair forever
#         self.asked_pairs = set()

#     def _phi(self, idx_i: int, idx_j: int) -> np.ndarray:
#         return self.X_cache[idx_i] - self.X_cache[idx_j]  # shape (D,)

#     def pick_next_pair(self, sample_pairs: int = 2000) -> Tuple[int, int, float]:
#         """
#         Choose pair (i, j) that maximizes predictive variance:
#             Var[y] = phi^T Sigma phi + sigma2
#         (We ignore exploitation here. You *could* add a term to bias toward
#          uncertain *and* balanced preference, but variance-only already drives exploration.)
#         """
#         rng = np.random.default_rng()
#         n = self.M

#         # generate candidate pairs
#         max_pairs_possible = n * (n - 1) // 2
#         if max_pairs_possible <= sample_pairs:
#             pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
#         else:
#             pairs = set()
#             while len(pairs) < sample_pairs:
#                 i = rng.integers(0, n)
#                 j = rng.integers(0, n)
#                 if i == j:
#                     continue
#                 a, b = (i, j) if i < j else (j, i)
#                 if a == b:
#                     continue
#                 # skip pairs we've already asked to reduce repetition
#                 if (a, b) in self.asked_pairs:
#                     continue
#                 pairs.add((a, b))
#             pairs = list(pairs)

#         best_score = -1.0
#         best_pair = (0, 1)

#         for (i, j) in pairs:
#             phi = self._phi(i, j)  # (D,)
#             # predictive variance S = phi^T Sigma phi + sigma2
#             S = float(phi @ (self.Sigma @ phi) + self.sigma2)
#             if S > best_score:
#                 best_score = S
#                 best_pair = (i, j)

#         # remember so we don't spam the same pair
#         self.asked_pairs.add(best_pair)

#         return best_pair[0], best_pair[1], best_score

#     def update_with_answer(self, idx_i: int, idx_j: int, picked_i: bool):
#         """
#         Perform a Kalman-style linear regression update on theta_hat, Sigma.

#         y = 1 if user picked movie i over movie j
#             0 otherwise
#         model y ≈ phi^T theta + N(0, sigma2)
#         """
#         y = 1.0 if picked_i else 0.0
#         phi = self._phi(idx_i, idx_j)  # shape (D,)

#         # prediction
#         pred = float(phi @ self.theta_hat)               # scalar
#         # innovation covariance
#         S = float(phi @ (self.Sigma @ phi) + self.sigma2)  # scalar, >0
#         # Kalman gain
#         K = (self.Sigma @ phi) / S                       # shape (D,)

#         # update mean
#         resid = (y - pred)
#         self.theta_hat = self.theta_hat + K * resid      # shape (D,)

#         # update covariance
#         # Sigma <- Sigma - K * phi^T * Sigma
#         # note phi^T Sigma is (1,D); K is (D,)
#         Sigma_phiT = (phi @ self.Sigma)                  # shape (D,)
#         self.Sigma = self.Sigma - np.outer(K, Sigma_phiT)

#     def recommend_topN(self, N: int = 10) -> List[Tuple[str, str, float]]:
#         """
#         Rank cached candidates by cosine similarity between theta_hat and movie vector.
#         """
#         theta_norm = np.linalg.norm(self.theta_hat) + 1e-12
#         t_hat = self.theta_hat / theta_norm  # (D,)

#         X_norms = np.linalg.norm(self.X_cache, axis=1, keepdims=True) + 1e-12
#         X_hat = self.X_cache / X_norms       # (M,D)

#         sims = X_hat @ t_hat                 # (M,)
#         order = np.argsort(-sims)[:N]

#         out = []
#         for idx in order:
#             out.append((
#                 self.movie_ids_cache[idx],
#                 self.titles_cache[idx],
#                 float(sims[idx]),
#             ))
#         return out

# ###############################################################################
# # Interactive CLI
# ###############################################################################

# if __name__ == "__main__":
#     collection_name = os.getenv("CHROMA_COLLECTION", "movie_tag_relevance_cos")

#     model = MoviePairBayesModel(
#         collection_name=collection_name,
#         sigma2_obs=0.05,        # how noisy we assume your answers are
#         max_candidates=9000,    # pull basically all movies in one go (if mem is ok)
#         prior_mean_path="/app/prior_mean.npy",
#         prior_cov_path="/app/prior_cov.npy",
#     )

#     print(f"[info] Loaded {len(model.movie_ids_cache)} candidate movies")
#     print(f"[info] Embedding dim = {model.dim}")
#     print("[info] We'll adaptively ask you to choose between pairs we are most unsure about.")

#     num_q = 10  # ask 10 pairwise questions
#     for step in range(num_q):
#         i, j, score = model.pick_next_pair(sample_pairs=2000)

#         movie_i_id = model.movie_ids_cache[i]
#         movie_j_id = model.movie_ids_cache[j]
#         movie_i_title = model.titles_cache[i]
#         movie_j_title = model.titles_cache[j]

#         print(f"\nQuestion {step+1}: which do you prefer?")
#         print(f"  (0) {movie_i_title} [{movie_i_id}]")
#         print(f"  (1) {movie_j_title} [{movie_j_id}]")
#         ans = input("Your choice [0/1]: ").strip()
#         picked_i = (ans == "0")

#         model.update_with_answer(i, j, picked_i)
#         cur_norm = np.linalg.norm(model.theta_hat)
#         print(f" -> updated ||theta_hat|| = {cur_norm:.4f}")

#     # final recs
#     print("\n[recs] computing movie recommendations …")
#     recs = model.recommend_topN(N=10)
#     print("\nYour top-10 right now:")
#     for mid, title, score in recs:
#         print(f"  {title} [{mid}]: {score:.4f}")
