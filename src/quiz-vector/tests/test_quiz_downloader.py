import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
import os
from pathlib import Path
from src.datapipeline.downloader import (
    get_chroma_client,
    log,
    download_prefix,
    stream_object,
    parse_lines,
    parse_movies,
    parse_tags,
    ingest_tag_relevance_to_chroma,
    ingest_tags_metadata_to_chroma,
    cli
)


class TestGetChromaClient:
    def test_http_client_when_host_and_port_set(self, monkeypatch):
        monkeypatch.setenv("CHROMA_SERVER_HOST", "localhost")
        monkeypatch.setenv("CHROMA_SERVER_PORT", "8000")

        with patch("src.datapipeline.downloader.chromadb.HttpClient") as mock_http:
            client = get_chroma_client()
            mock_http.assert_called_once_with(host="localhost", port=8000)

    def test_persistent_client_when_no_host_port(self, monkeypatch):
        monkeypatch.delenv("CHROMA_SERVER_HOST", raising=False)
        monkeypatch.delenv("CHROMA_SERVER_PORT", raising=False)
        monkeypatch.setenv("CHROMA_PATH", "./test_chroma")

        with patch("src.datapipeline.downloader.chromadb.PersistentClient") as mock_persistent:
            client = get_chroma_client()
            mock_persistent.assert_called_once_with(path="./test_chroma")

    def test_persistent_client_default_path(self, monkeypatch):
        monkeypatch.delenv("CHROMA_SERVER_HOST", raising=False)
        monkeypatch.delenv("CHROMA_SERVER_PORT", raising=False)
        monkeypatch.delenv("CHROMA_PATH", raising=False)

        with patch("src.datapipeline.downloader.chromadb.PersistentClient") as mock_persistent:
            client = get_chroma_client()
            mock_persistent.assert_called_once_with(path="./chroma_db")


class TestLog:
    def test_log_output(self, capsys):
        log("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.out
        assert "[LOAD" in captured.out


class TestDownloadPrefix:
    @patch("src.datapipeline.downloader.storage.Client")
    @patch("src.datapipeline.downloader.Path")
    def test_no_blobs_found(self, mock_path, mock_storage_client, tmp_path):
        mock_bucket = Mock()
        mock_bucket.list_blobs.return_value = []
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client

        mock_path_obj = Mock()
        mock_path_obj.resolve.return_value = mock_path_obj
        mock_path_obj.mkdir = Mock()
        mock_path.return_value = mock_path_obj

        download_prefix("test-bucket", "test-prefix", str(tmp_path))

        mock_bucket.list_blobs.assert_called_once_with(prefix="test-prefix")

    @patch("src.datapipeline.downloader.storage.Client")
    @patch("src.datapipeline.downloader.tqdm")
    def test_download_multiple_blobs(self, mock_tqdm, mock_storage_client, tmp_path):
        mock_blob1 = Mock()
        mock_blob1.name = "prefix/file1.txt"
        mock_blob2 = Mock()
        mock_blob2.name = "prefix/file2.txt"

        mock_bucket = Mock()
        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client

        mock_tqdm.return_value = [mock_blob1, mock_blob2]

        out_dir = tmp_path / "output"
        download_prefix("test-bucket", "prefix", str(out_dir))

        assert mock_blob1.download_to_filename.called
        assert mock_blob2.download_to_filename.called


class TestStreamObject:
    @patch("src.datapipeline.downloader.storage.Client")
    def test_stream_object_success(self, mock_storage_client):
        mock_blob = Mock()
        mock_blob.download_as_bytes.return_value = b"test data"
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client

        result = stream_object("test-bucket", "test-object")

        assert result == b"test data"
        mock_client.bucket.assert_called_once_with("test-bucket")
        mock_bucket.blob.assert_called_once_with("test-object")
        mock_blob.download_as_bytes.assert_called_once()


class TestParseLines:
    def test_parse_lines_basic(self):
        raw = b"1||2||0.5\n3||4||0.8"
        result = list(parse_lines(raw))
        assert len(result) == 2
        assert result[0] == (1, 2, 0.5)
        assert result[1] == (3, 4, 0.8)

    def test_parse_lines_various_separators(self):
        raw = b"1\t2\t0.5\n3,4,0.8\n5 6 0.9"
        result = list(parse_lines(raw))
        assert len(result) == 3
        assert result[0] == (1, 2, 0.5)
        assert result[1] == (3, 4, 0.8)
        assert result[2] == (5, 6, 0.9)

    def test_parse_lines_skip_header(self):
        raw = b"movie_id||tag_id||relevance\n1||2||0.5"
        result = list(parse_lines(raw))
        assert len(result) == 1
        assert result[0] == (1, 2, 0.5)

    def test_parse_lines_skip_empty_lines(self):
        raw = b"1||2||0.5\n\n3||4||0.8"
        result = list(parse_lines(raw))
        assert len(result) == 2

    def test_parse_lines_skip_malformed(self):
        raw = b"1||2||0.5\nbad line\n3||4||0.8"
        result = list(parse_lines(raw))
        assert len(result) == 2


class TestParseMovies:
    def test_parse_movies_basic(self):
        raw = b"1\tToy Story\t862\n2\tJumanji\t8844"
        result = parse_movies(raw)
        assert len(result) == 2
        assert result[1] == "Toy Story"
        assert result[2] == "Jumanji"

    def test_parse_movies_skip_empty_lines(self):
        raw = b"1\tToy Story\n\n2\tJumanji"
        result = parse_movies(raw)
        assert len(result) == 2

    def test_parse_movies_skip_malformed(self):
        raw = b"1\tToy Story\nbadline\n2\tJumanji"
        result = parse_movies(raw)
        assert len(result) == 2


class TestParseTags:
    def test_parse_tags_basic(self):
        raw = b"1\taction\t500\n2\tcomedy\t300"
        result = parse_tags(raw)
        assert len(result) == 2
        assert result[1] == "action"
        assert result[2] == "comedy"

    def test_parse_tags_skip_empty_lines(self):
        raw = b"1\taction\t500\n\n2\tcomedy\t300"
        result = parse_tags(raw)
        assert len(result) == 2

    def test_parse_tags_skip_malformed(self):
        raw = b"1\taction\t500\nbadline\n2\tcomedy\t300"
        result = parse_tags(raw)
        assert len(result) == 2


class TestIngestTagRelevanceToChroma:
    @patch("src.datapipeline.downloader.stream_object")
    @patch("src.datapipeline.downloader.get_chroma_client")
    def test_ingest_creates_collection(self, mock_chroma_client, mock_stream, tmp_path):
        mock_stream.return_value = b"1||2||0.5\n1||3||0.8"

        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_collection.side_effect = Exception("not found")
        mock_client.create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client

        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        with patch.dict(os.environ, {"LOG_DIR": str(log_dir)}):
            ingest_tag_relevance_to_chroma(
                bucket="test-bucket",
                object_name="test.dat",
                batch_size=1000
            )

        mock_client.create_collection.assert_called_once()
        assert mock_collection.add.called


class TestIngestTagsMetadataToChroma:
    @patch("src.datapipeline.downloader.stream_object")
    @patch("src.datapipeline.downloader.get_chroma_client")
    def test_ingest_tags_metadata(self, mock_chroma_client, mock_stream):
        mock_stream.return_value = b"1\taction\t500\n2\tcomedy\t300"

        mock_collection = Mock()
        mock_client = Mock()
        mock_client.get_collection.side_effect = Exception("not found")
        mock_client.create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client

        ingest_tags_metadata_to_chroma(
            bucket="test-bucket",
            tags_object_name="tags.dat"
        )

        mock_client.create_collection.assert_called_once()
        assert mock_collection.add.called


class TestCli:
    @patch("src.datapipeline.downloader.download_prefix")
    @patch("sys.argv", ["downloader.py", "--bucket", "test-bucket"])
    def test_cli_download_prefix(self, mock_download):
        cli()
        assert mock_download.called

    @patch("src.datapipeline.downloader.ingest_tag_relevance_to_chroma")
    @patch("sys.argv", ["downloader.py", "--bucket", "test-bucket", "--to_chroma"])
    def test_cli_to_chroma(self, mock_ingest):
        cli()
        assert mock_ingest.called

    @patch("src.datapipeline.downloader.ingest_tags_metadata_to_chroma")
    @patch("sys.argv", ["downloader.py", "--bucket", "test-bucket", "--to_tagmeta"])
    def test_cli_to_tagmeta(self, mock_ingest):
        cli()
        assert mock_ingest.called