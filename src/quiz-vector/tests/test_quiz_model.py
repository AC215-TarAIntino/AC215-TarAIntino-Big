import numpy as np
import pytest

from quiz_service.model import FullCovarianceTasteModel


@pytest.fixture
def sample_prior():
    """Create a simple prior for testing."""
    D = 10
    prior_mean = np.random.randn(D) * 0.1 + 0.5
    prior_cov = np.eye(D) * 0.1
    return prior_mean, prior_cov


@pytest.fixture
def sample_tags():
    """Create sample quiz tags."""
    return [(0, "funny"), (1, "dark"), (2, "romantic"), (3, "action"), (4, "drama")]


@pytest.fixture
def sample_tagid2col():
    """Create sample tag ID to column mapping."""
    return {i: i for i in range(10)}


class TestFullCovarianceTasteModel:
    def test_model_initialization(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        assert model.D == 10
        assert model.K == 5  # 5 quiz tags
        assert model.sigma2 == 0.05
        assert len(model.quiz_texts) == 5
        assert model.quiz_texts[0] == "funny"

    def test_model_initialization_with_target_questions(
        self, sample_prior, sample_tags, sample_tagid2col
    ):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            target_questions=3,
        )

        assert model.target == 3

    def test_model_target_clamping_min(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            target_questions=0,  # Should clamp to 1
        )

        assert model.target == 1

    def test_model_target_clamping_max(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            target_questions=100,  # Should clamp to K=5
        )

        assert model.target == 5

    def test_model_no_valid_tags_raises_error(self, sample_prior):
        prior_mean, prior_cov = sample_prior
        # Tags that don't exist in tagid2col
        invalid_tags = [(100, "missing"), (200, "also_missing")]
        tagid2col = {i: i for i in range(10)}

        with pytest.raises(ValueError, match="No quiz tags mapped"):
            FullCovarianceTasteModel(
                prior_mean=prior_mean,
                prior_cov=prior_cov,
                tagid2col=tagid2col,
                quiz_tags=invalid_tags,
            )

    def test_pick_next_quiz_tag_initial(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        # Set specific variances to test selection
        prior_cov = np.eye(10) * 0.1
        prior_cov[2, 2] = 1.0  # Highest variance

        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        # Should pick the tag with highest variance (tag 2)
        k = model.pick_next_quiz_tag()
        assert k == 2

    def test_pick_next_quiz_tag_excludes_asked(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        prior_cov = np.eye(10) * 0.1
        prior_cov[0, 0] = 1.0  # Highest variance
        prior_cov[1, 1] = 0.8  # Second highest

        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        # Mark first tag as asked
        model.asked_mask[0] = True

        # Should now pick tag with second-highest variance
        k = model.pick_next_quiz_tag()
        assert k == 1

    def test_current_question_payload(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        payload = model.current_question_payload(0)
        assert payload["question_id"] == 0
        assert payload["tag_id"] == 0
        assert payload["tag_label"] == "funny"
        assert payload["scale"] == {"min": 1, "max": 10}

    def test_update_with_answer(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        # Store initial state
        initial_mean = model.theta_hat.copy()
        initial_cov = model.Sigma.copy()

        # Answer first question with rating of 8 (out of 10)
        model.update_with_answer(0, 8.0)

        # Verify state changed
        assert not np.allclose(model.theta_hat, initial_mean)
        assert not np.allclose(model.Sigma, initial_cov)

        # Verify the tag was marked as asked
        assert model.asked_mask[0]

    def test_update_with_answer_clamps_rating(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        # Test with out-of-range values
        model.update_with_answer(0, 15.0)  # Should clamp to 10
        assert model.asked_mask[0]

        model.update_with_answer(1, -5.0)  # Should clamp to 0
        assert model.asked_mask[1]

    def test_update_preserves_symmetry(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        model.update_with_answer(0, 7.0)

        # Covariance should remain symmetric
        assert np.allclose(model.Sigma, model.Sigma.T)

    def test_export_taste_vector(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        taste_vec = model.export_taste_vector()

        assert isinstance(taste_vec, np.ndarray)
        assert taste_vec.shape == (10,)

        # Should be a copy, not a reference
        taste_vec[0] = 999.0
        assert model.theta_hat[0] != 999.0

    def test_quiz_status(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
            target_questions=3,
        )

        status = model.quiz_status()
        assert status["asked"] == 0
        assert status["total"] == 3

        # Answer one question
        model.update_with_answer(0, 7.0)

        status = model.quiz_status()
        assert status["asked"] == 1
        assert status["total"] == 3

    def test_is_complete(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
            target_questions=2,
        )

        assert not model.is_complete()

        # Answer first question
        model.update_with_answer(0, 7.0)
        assert not model.is_complete()

        # Answer second question
        model.update_with_answer(1, 8.0)
        assert model.is_complete()

    def test_multiple_updates_sequential(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        # Simulate a full quiz session
        for i in range(3):
            k = model.pick_next_quiz_tag()
            model.current_question_payload(k)
            model.update_with_answer(k, float(5 + i))

        # Check that 3 questions were asked
        assert model.quiz_status()["asked"] == 3

        # Verify asked mask
        assert model.asked_mask.sum() == 3

    def test_variance_reduction_after_update(self, sample_prior, sample_tags, sample_tagid2col):
        prior_mean, prior_cov = sample_prior
        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=sample_tags,
            sigma2=0.05,
        )

        # Get initial variance for tag 0
        j = model.quiz_cols[0]
        initial_var = model.Sigma[j, j]

        # Update with answer
        model.update_with_answer(0, 7.0)

        # Variance should decrease after observing data
        updated_var = model.Sigma[j, j]
        assert updated_var < initial_var

    def test_model_with_partial_tag_mapping(self, sample_prior, sample_tagid2col):
        prior_mean, prior_cov = sample_prior

        # Mix of valid and invalid tags
        mixed_tags = [
            (0, "valid1"),
            (1, "valid2"),
            (100, "invalid1"),  # Not in tagid2col
            (2, "valid3"),
        ]

        model = FullCovarianceTasteModel(
            prior_mean=prior_mean,
            prior_cov=prior_cov,
            tagid2col=sample_tagid2col,
            quiz_tags=mixed_tags,
            sigma2=0.05,
        )

        # Should only have 3 valid tags
        assert model.K == 3
        assert len(model.quiz_texts) == 3
        assert "invalid1" not in model.quiz_texts
