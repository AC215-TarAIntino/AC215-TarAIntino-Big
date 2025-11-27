from unittest.mock import Mock, patch

import pytest
from src.datapipeline.uploader import log, main, upload_dir


class TestLog:
    def test_log_output(self, capsys):
        log("test message")
        captured = capsys.readouterr()
        assert "test message" in captured.out
        assert "[STORE" in captured.out


class TestUploadDir:
    @patch("src.datapipeline.uploader.storage.Client")
    @patch("src.datapipeline.uploader.tqdm")
    def test_upload_dir_no_files(self, mock_tqdm, mock_storage_client, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        upload_dir(str(empty_dir), "test-bucket", "test-prefix")

        mock_storage_client.assert_not_called()

    @patch("src.datapipeline.uploader.storage.Client")
    @patch("src.datapipeline.uploader.tqdm")
    def test_upload_dir_with_files(self, mock_tqdm, mock_storage_client, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        file1 = test_dir / "file1.txt"
        file1.write_text("content1")
        file2 = test_dir / "file2.txt"
        file2.write_text("content2")

        mock_blob = Mock()
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client

        mock_tqdm.return_value = [file1, file2]

        upload_dir(str(test_dir), "test-bucket", "test-prefix")

        mock_client.bucket.assert_called_once_with("test-bucket")
        assert mock_blob.upload_from_filename.call_count == 2

    @patch("src.datapipeline.uploader.storage.Client")
    @patch("src.datapipeline.uploader.tqdm")
    def test_upload_dir_with_nested_files(self, mock_tqdm, mock_storage_client, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        nested_dir = test_dir / "nested"
        nested_dir.mkdir()

        file1 = nested_dir / "file1.txt"
        file1.write_text("content1")

        mock_blob = Mock()
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client

        mock_tqdm.return_value = [file1]

        upload_dir(str(test_dir), "test-bucket", "prefix")

        mock_bucket.blob.assert_called()
        call_args = mock_bucket.blob.call_args[0][0]
        assert "nested/file1.txt" in call_args

    @patch("src.datapipeline.uploader.storage.Client")
    @patch("src.datapipeline.uploader.tqdm")
    def test_upload_dir_empty_prefix(self, mock_tqdm, mock_storage_client, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        file1 = test_dir / "file1.txt"
        file1.write_text("content1")

        mock_blob = Mock()
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client = Mock()
        mock_client.bucket.return_value = mock_bucket
        mock_storage_client.return_value = mock_client

        mock_tqdm.return_value = [file1]

        upload_dir(str(test_dir), "test-bucket", "")

        mock_bucket.blob.assert_called_with("file1.txt")


class TestMain:
    @patch("src.datapipeline.uploader.upload_dir")
    @patch("sys.argv", ["uploader.py", "--local_dir", "/tmp/test", "--bucket", "test-bucket"])
    def test_main_with_all_args(self, mock_upload):
        main()
        mock_upload.assert_called_once()

    @patch("src.datapipeline.uploader.upload_dir")
    @patch.dict("os.environ", {"GCS_BUCKET": "env-bucket", "GCS_PREFIX": "env-prefix"})
    @patch("sys.argv", ["uploader.py", "--local_dir", "/tmp/test"])
    def test_main_with_env_vars(self, mock_upload):
        main()
        mock_upload.assert_called_once_with("/tmp/test", "env-bucket", "env-prefix")

    @patch("sys.argv", ["uploader.py", "--local_dir", "/tmp/test"])
    def test_main_missing_bucket(self):
        with pytest.raises(AssertionError):
            main()
