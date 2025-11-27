import pytest
from unittest.mock import Mock, patch, mock_open
import numpy as np
import json
from src.quiz_service.config import (
    get_chroma_client,
    get_collection,
    load_tagid2col,
    get_tagid2col,
    get_prior_mean,
    get_prior_cov,
    QUIZ_TAGS,
    PRIOR_MEAN_PATH,
    PRIOR_COV_PATH,
    CHROMA_COLLECTION,
    TAG_INDEX_JSON
)


class TestGetChromaClient:
    def test_http_client_when_host_and_port_set(self, monkeypatch):
        monkeypatch.setenv("CHROMA_SERVER_HOST", "localhost")
        monkeypatch.setenv("CHROMA_SERVER_PORT", "8000")

        with patch("src.quiz_service.config.chromadb.HttpClient") as mock_http:
            client = get_chroma_client()
            mock_http.assert_called_once_with(host="localhost", port=8000)

    def test_persistent_client_when_no_host_port(self, monkeypatch):
        monkeypatch.delenv("CHROMA_SERVER_HOST", raising=False)
        monkeypatch.delenv("CHROMA_SERVER_PORT", raising=False)
        monkeypatch.setenv("CHROMA_PATH", "./test_chroma")

        with patch("src.quiz_service.config.chromadb.PersistentClient") as mock_persistent:
            client = get_chroma_client()
            mock_persistent.assert_called_once_with(path="./test_chroma")

    def test_persistent_client_default_path(self, monkeypatch):
        monkeypatch.delenv("CHROMA_SERVER_HOST", raising=False)
        monkeypatch.delenv("CHROMA_SERVER_PORT", raising=False)
        monkeypatch.delenv("CHROMA_PATH", raising=False)

        with patch("src.quiz_service.config.chromadb.PersistentClient") as mock_persistent:
            client = get_chroma_client()
            mock_persistent.assert_called_once_with(path="./chroma_db")


class TestGetCollection:
    @patch("src.quiz_service.config.get_chroma_client")
    def test_get_collection_success(self, mock_get_client):
        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        get_collection.cache_clear()
        collection = get_collection()

        mock_client.get_collection.assert_called_once_with(CHROMA_COLLECTION)
        assert collection == mock_collection

    @patch("src.quiz_service.config.get_chroma_client")
    def test_get_collection_cached(self, mock_get_client):
        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        get_collection.cache_clear()
        collection1 = get_collection()
        collection2 = get_collection()

        mock_client.get_collection.assert_called_once()
        assert collection1 == collection2


class TestLoadTagid2col:
    def test_load_tagid2col_success(self, tmp_path):
        tag_data = {"tag_ids_sorted": [1, 2, 3, 4, 5]}
        tag_file = tmp_path / "tags.json"
        tag_file.write_text(json.dumps(tag_data))

        result = load_tagid2col(str(tag_file))

        assert result == {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}

    def test_load_tagid2col_empty_list(self, tmp_path):
        tag_data = {"tag_ids_sorted": []}
        tag_file = tmp_path / "tags.json"
        tag_file.write_text(json.dumps(tag_data))

        result = load_tagid2col(str(tag_file))

        assert result == {}

    def test_load_tagid2col_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_tagid2col("/nonexistent/path/tags.json")


class TestGetTagid2col:
    @patch("src.quiz_service.config.load_tagid2col")
    def test_get_tagid2col_success(self, mock_load):
        mock_load.return_value = {1: 0, 2: 1, 3: 2}

        get_tagid2col.cache_clear()
        result = get_tagid2col()

        mock_load.assert_called_once_with(TAG_INDEX_JSON)
        assert result == {1: 0, 2: 1, 3: 2}

    @patch("src.quiz_service.config.load_tagid2col")
    def test_get_tagid2col_cached(self, mock_load):
        mock_load.return_value = {1: 0, 2: 1, 3: 2}

        get_tagid2col.cache_clear()
        result1 = get_tagid2col()
        result2 = get_tagid2col()

        mock_load.assert_called_once()
        assert result1 == result2


class TestGetPriorMean:
    @patch("src.quiz_service.config.np.load")
    def test_get_prior_mean_success(self, mock_np_load):
        mock_array = np.array([1.0, 2.0, 3.0])
        mock_np_load.return_value = mock_array

        get_prior_mean.cache_clear()
        result = get_prior_mean()

        mock_np_load.assert_called_once_with(PRIOR_MEAN_PATH)
        np.testing.assert_array_equal(result, mock_array)

    @patch("src.quiz_service.config.np.load")
    def test_get_prior_mean_cached(self, mock_np_load):
        mock_array = np.array([1.0, 2.0, 3.0])
        mock_np_load.return_value = mock_array

        get_prior_mean.cache_clear()
        result1 = get_prior_mean()
        result2 = get_prior_mean()

        mock_np_load.assert_called_once()
        np.testing.assert_array_equal(result1, result2)


class TestGetPriorCov:
    @patch("src.quiz_service.config.np.load")
    def test_get_prior_cov_success(self, mock_np_load):
        mock_array = np.eye(3)
        mock_np_load.return_value = mock_array

        get_prior_cov.cache_clear()
        result = get_prior_cov()

        mock_np_load.assert_called_once_with(PRIOR_COV_PATH)
        np.testing.assert_array_equal(result, mock_array)

    @patch("src.quiz_service.config.np.load")
    def test_get_prior_cov_cached(self, mock_np_load):
        mock_array = np.eye(3)
        mock_np_load.return_value = mock_array

        get_prior_cov.cache_clear()
        result1 = get_prior_cov()
        result2 = get_prior_cov()

        mock_np_load.assert_called_once()
        np.testing.assert_array_equal(result1, result2)


class TestQuizTags:
    def test_quiz_tags_structure(self):
        assert isinstance(QUIZ_TAGS, list)
        assert len(QUIZ_TAGS) > 0

        for item in QUIZ_TAGS:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], int)
            assert isinstance(item[1], str)

    def test_quiz_tags_no_duplicates(self):
        tag_ids = [tag[0] for tag in QUIZ_TAGS]
        assert len(tag_ids) == len(set(tag_ids))

        tag_names = [tag[1] for tag in QUIZ_TAGS]
        assert len(tag_names) == len(set(tag_names))


class TestConstants:
    def test_prior_mean_path_default(self, monkeypatch):
        monkeypatch.delenv("PRIOR_MEAN_PATH", raising=False)
        from importlib import reload
        import src.quiz_service.config as config_module
        reload(config_module)
        assert config_module.PRIOR_MEAN_PATH == "/app/prior_mean.npy"

    def test_prior_cov_path_default(self, monkeypatch):
        monkeypatch.delenv("PRIOR_COV_PATH", raising=False)
        from importlib import reload
        import src.quiz_service.config as config_module
        reload(config_module)
        assert config_module.PRIOR_COV_PATH == "/app/prior_cov.npy"

    def test_chroma_collection_default(self, monkeypatch):
        monkeypatch.delenv("CHROMA_COLLECTION", raising=False)
        from importlib import reload
        import src.quiz_service.config as config_module
        reload(config_module)
        assert config_module.CHROMA_COLLECTION == "movie_tag_relevance_cos"