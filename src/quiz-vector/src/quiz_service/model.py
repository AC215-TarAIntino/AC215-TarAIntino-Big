# quiz_service/model.py


import numpy as np


class FullCovarianceTasteModel:
    def __init__(
        self,
        prior_mean: np.ndarray,
        prior_cov: np.ndarray,
        tagid2col: dict[int, int],
        quiz_tags: list[tuple[int, str]],
        sigma2: float = 0.05,
        target_questions: int | None = None,
    ):
        self.D = prior_mean.shape[0]
        self.theta_hat = prior_mean.astype(np.float64).copy()
        self.Sigma = prior_cov.astype(np.float64).copy()
        self.sigma2 = float(sigma2)

        quiz_cols, quiz_texts, quiz_ids = [], [], []
        for tid, txt in quiz_tags:
            if tid in tagid2col:
                quiz_cols.append(tagid2col[tid])
                quiz_texts.append(txt)
                quiz_ids.append(tid)

        if not quiz_cols:
            raise ValueError("No quiz tags mapped into embedding space.")

        self.quiz_cols = np.array(quiz_cols, dtype=int)
        self.quiz_texts = list(quiz_texts)
        self.quiz_ids = list(quiz_ids)
        self.K = len(self.quiz_cols)
        self.asked_mask = np.zeros(self.K, dtype=bool)
        self.target = int(target_questions) if target_questions is not None else self.K

        # set the target (how many questions to ask)
        if target_questions is None:
            self.target = self.K
        else:
            # clamp to [1, K]
            self.target = max(1, min(int(target_questions), self.K))

    def pick_next_quiz_tag(self) -> int:
        variances = np.array([self.Sigma[j, j] for j in self.quiz_cols], dtype=np.float64)
        variances[self.asked_mask] = -1e9
        return int(np.argmax(variances))

    def current_question_payload(self, k: int) -> dict:
        return {
            "question_id": k,
            "tag_id": int(self.quiz_ids[k]),
            "tag_label": self.quiz_texts[k],
            "scale": {"min": 1, "max": 10},
        }

    def update_with_answer(self, k: int, answer_1to10: float):
        j = int(self.quiz_cols[k])
        y = max(0.0, min(1.0, float(answer_1to10) / 10.0))

        theta_j = self.theta_hat[j]
        v_jj = self.Sigma[j, j]
        denom = v_jj + self.sigma2

        k_vec = self.Sigma[:, j] / denom
        self.theta_hat = self.theta_hat + k_vec * (y - theta_j)
        self.Sigma = self.Sigma - np.outer(k_vec, self.Sigma[j, :])
        self.Sigma = 0.5 * (self.Sigma + self.Sigma.T)
        self.asked_mask[k] = True

    def export_taste_vector(self) -> np.ndarray:
        return self.theta_hat.copy()

    def quiz_status(self) -> dict:
        asked = int(self.asked_mask.sum())
        return {"asked": asked, "total": int(self.target)}

    def is_complete(self) -> bool:
        return int(self.asked_mask.sum()) >= int(self.target)
