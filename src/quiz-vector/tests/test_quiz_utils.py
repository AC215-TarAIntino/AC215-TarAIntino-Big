import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from pathlib import Path
from src.quiz_service.utils import _compute_and_save_prior_if_needed, topN_from_matrix
from src.quiz_service.config import PRIOR_MEAN_PATH, PRIOR_COV_PATH


class TestComputeAndSavePriorIfNeeded:
    @patch("src.quiz_service.utils.Path")
    def test_skip_when_files_exist(self, mock_path_cls):
        mock_mean_path = Mock()
        mock_mean_path.exists.return_value = True
        mock_cov_path = Mock()
        mock_cov_path.exists.return_value = True

        mock_path_cls.side_effect = [mock_mean_path, mock_cov_path]

        _compute_and_save_prior_if_needed()

        mock_mean_path.exists.assert_called_once()
        mock_cov_path.exists.assert_called_once()

    @patch("src.quiz_service.utils.get_collection")
    @patch("src.quiz_service.utils.np.save")
    @patch("src.quiz_service.utils.Path")
    def test_compute_and_save_when_files_missing(self, mock_path_cls, mock_np_save, mock_get_collection):
        mock_mean_path = Mock()
        mock_mean_path.exists.return_value = False
        mock_cov_path = Mock()
        mock_cov_path.exists.return_value = False

        mock_path_cls.side_effect = [mock_mean_path, mock_cov_path]

        mock_collection = Mock()
        embeddings = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
        mock_collection.peek.return_value = {"embeddings": embeddings}
        mock_get_collection.return_value = mock_collection

        _compute_and_save_prior_if_needed()

        mock_collection.peek.assert_called_once_with(20000)
        assert mock_np_save.call_count == 2

    @patch("src.quiz_service.utils.get_collection")
    @patch("src.quiz_service.utils.Path")
    def test_raise_error_when_no_embeddings(self, mock_path_cls, mock_get_collection):
        mock_mean_path = Mock()
        mock_mean_path.exists.return_value = False
        mock_cov_path = Mock()
        mock_cov_path.exists.return_value = False

        mock_path_cls.side_effect = [mock_mean_path, mock_cov_path]

        mock_collection = Mock()
        mock_collection.peek.return_value = {"embeddings": None}
        mock_get_collection.return_value = mock_collection

        with pytest.raises(RuntimeError, match="No embeddings in Chroma"):
            _compute_and_save_prior_if_needed()

    @patch("src.quiz_service.utils.get_collection")
    @patch("src.quiz_service.utils.Path")
    def test_raise_error_when_empty_embeddings(self, mock_path_cls, mock_get_collection):
        mock_mean_path = Mock()
        mock_mean_path.exists.return_value = False
        mock_cov_path = Mock()
        mock_cov_path.exists.return_value = False

        mock_path_cls.side_effect = [mock_mean_path, mock_cov_path]

        mock_collection = Mock()
        mock_collection.peek.return_value = {"embeddings": []}
        mock_get_collection.return_value = mock_collection

        with pytest.raises(RuntimeError, match="No embeddings in Chroma"):
            _compute_and_save_prior_if_needed()

    @patch("src.quiz_service.utils.get_collection")
    @patch("src.quiz_service.utils.np.save")
    @patch("src.quiz_service.utils.Path")
    def test_adds_regularization_to_covariance(self, mock_path_cls, mock_np_save, mock_get_collection):
        mock_mean_path = Mock()
        mock_mean_path.exists.return_value = False
        mock_cov_path = Mock()
        mock_cov_path.exists.return_value = False

        mock_path_cls.side_effect = [mock_mean_path, mock_cov_path]

        mock_collection = Mock()
        embeddings = [[1.0, 0.0], [0.0, 1.0]]
        mock_collection.peek.return_value = {"embeddings": embeddings}
        mock_get_collection.return_value = mock_collection

        _compute_and_save_prior_if_needed()

        assert mock_np_save.call_count == 2
        saved_cov = mock_np_save.call_args_list[1][0][1]
        assert np.min(np.diag(saved_cov)) >= 1e-3


class TestTopNFromMatrix:
    def test_topn_basic(self):
        theta_hat = np.array([1.0, 0.0, 0.0])
        X = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.9, 0.1, 0.0]
        ])
        ids = ["1", "2", "3", "4"]
        metas = [
            {"movieId": 1, "title": "Movie 1"},
            {"movieId": 2, "title": "Movie 2"},
            {"movieId": 3, "title": "Movie 3"},
            {"movieId": 4, "title": "Movie 4"}
        ]

        result = topN_from_matrix(theta_hat, X, ids, metas, N=2)

        assert len(result) == 2
        assert result[0]["movie_id"] == "1"
        assert result[0]["title"] == "Movie 1"
        assert result[0]["score"] > result[1]["score"]

    def test_topn_returns_correct_count(self):
        theta_hat = np.array([1.0, 1.0])
        X = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0]
        ])
        ids = ["1", "2", "3"]
        metas = [{"title": "Movie 1"}, {"title": "Movie 2"}, {"title": "Movie 3"}]

        result = topN_from_matrix(theta_hat, X, ids, metas, N=2)

        assert len(result) == 2

    def test_topn_all_results_when_n_larger(self):
        theta_hat = np.array([1.0, 0.0])
        X = np.array([[1.0, 0.0], [0.0, 1.0]])
        ids = ["1", "2"]
        metas = [{"title": "Movie 1"}, {"title": "Movie 2"}]

        result = topN_from_matrix(theta_hat, X, ids, metas, N=10)

        assert len(result) == 2

    def test_topn_normalizes_vectors(self):
        theta_hat = np.array([2.0, 0.0])
        X = np.array([[2.0, 0.0], [0.0, 2.0]])
        ids = ["1", "2"]
        metas = [{"title": "Movie 1"}, {"title": "Movie 2"}]

        result = topN_from_matrix(theta_hat, X, ids, metas, N=2)

        assert result[0]["score"] <= 1.0
        assert result[0]["score"] >= -1.0

    def test_topn_handles_missing_metadata(self):
        theta_hat = np.array([1.0, 0.0])
        X = np.array([[1.0, 0.0]])
        ids = ["1"]
        metas = [None]

        result = topN_from_matrix(theta_hat, X, ids, metas, N=1)

        assert len(result) == 1
        assert "Movie 1" in result[0]["title"]

    def test_topn_handles_missing_title_in_metadata(self):
        theta_hat = np.array([1.0, 0.0])
        X = np.array([[1.0, 0.0]])
        ids = ["1"]
        metas = [{"movieId": 1}]

        result = topN_from_matrix(theta_hat, X, ids, metas, N=1)

        assert len(result) == 1
        assert "Movie 1" in result[0]["title"]

    def test_topn_handles_zero_norm_theta(self):
        theta_hat = np.array([0.0, 0.0])
        X = np.array([[1.0, 0.0], [0.0, 1.0]])
        ids = ["1", "2"]
        metas = [{"title": "Movie 1"}, {"title": "Movie 2"}]

        result = topN_from_matrix(theta_hat, X, ids, metas, N=2)

        assert len(result) == 2
        for item in result:
            assert abs(item["score"]) < 0.01

    def test_topn_handles_zero_norm_embeddings(self):
        theta_hat = np.array([1.0, 0.0])
        X = np.array([[0.0, 0.0], [1.0, 0.0]])
        ids = ["1", "2"]
        metas = [{"title": "Movie 1"}, {"title": "Movie 2"}]

        result = topN_from_matrix(theta_hat, X, ids, metas, N=2)

        assert len(result) == 2

    def test_topn_returns_scores_in_descending_order(self):
        theta_hat = np.array([1.0, 0.0, 0.0])
        X = np.array([
            [0.5, 0.5, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ])
        ids = ["1", "2", "3"]
        metas = [{"title": f"Movie {i}"} for i in range(1, 4)]

        result = topN_from_matrix(theta_hat, X, ids, metas, N=3)

        assert len(result) == 3
        for i in range(len(result) - 1):
            assert result[i]["score"] >= result[i + 1]["score"]