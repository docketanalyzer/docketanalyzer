from pathlib import Path

import botocore
import pytest

from docketanalyzer import env, load_clients
from docketanalyzer.services.s3 import S3


def test_psql_connection():
    """Test the Postgres service."""
    key_check = bool(env.APP_HOST) or bool(env.POSTGRES_HOST)
    assert key_check, "APP_HOST or POSTGRES_HOST is not set"

    key_check = bool(env.POSTGRES_PASSWORD)
    assert key_check, "POSTGRES_PASSWORD is not set"

    db_service = load_clients("db", return_service=True)

    assert db_service.status(), "Postgres could not connect"


@pytest.mark.local
def test_elastic_connection():
    """Test the Elasticsearch service."""
    es_service = load_clients("es", return_service=True)

    assert es_service.status(), "Elasticsearch could not connect"


@pytest.mark.local
def test_redis_connection():
    """Test the Redis service."""
    redis_service = load_clients("redis", return_service=True)

    assert redis_service.status(), "Redis could not connect"


def test_s3_connection():
    """Test the S3 service connection."""
    key_check = bool(env.AWS_S3_BUCKET_NAME)
    assert key_check, "AWS_S3_BUCKET_NAME is not set"
    key_check = bool(env.AWS_ACCESS_KEY_ID)
    assert key_check, "AWS_ACCESS_KEY_ID is not set"
    key_check = bool(env.AWS_SECRET_ACCESS_KEY)
    assert key_check, "AWS_SECRET_ACCESS_KEY is not set"
    key_check = bool(env.AWS_S3_ENDPOINT_URL)
    assert key_check, "AWS_S3_ENDPOINT_URL is not set"

    s3 = load_clients("s3", return_service=True)

    assert s3.status(), "S3 could not connect"


def test_s3_upload_and_delete(temp_data_dir):
    """Test the S3 upload and delete functionality."""
    s3 = load_clients("s3")

    # Create a temporary file
    path = temp_data_dir / "test.txt"
    path.write_text("hello")

    # Upload the file to S3
    s3_key = s3.upload(path)

    assert s3_key is not None

    path.unlink()

    assert not path.exists()

    # Download the file from S3
    s3.download(s3_key)

    assert path.exists()
    assert path.read_text() == "hello"

    # Delete the file from S3
    s3.delete(s3_key)

    error = False
    try:
        s3.download(s3_key)
    except botocore.exceptions.ClientError:
        error = True
    assert error


def test_s3_push_and_pull(temp_data_dir):
    """Test the S3 push and pull functionality."""
    s3 = load_clients("s3")

    # Create a temporary file
    path = temp_data_dir / "test.txt"
    path.write_text("hello")

    # Push the file to S3
    s3.push(temp_data_dir)
    path.unlink()

    assert not path.exists()

    # Pull the file from S3
    s3.pull(temp_data_dir)

    assert path.exists()
    assert path.read_text() == "hello"

    # Push and pull with delete = True
    path.unlink()

    assert not path.exists()

    s3.push(temp_data_dir, delete=True)
    s3.pull(temp_data_dir)

    assert not path.exists()


def test_prepare_paths_defaults(temp_data_dir):
    """`_prepare_paths` defaults missing paths to `.` and errors if all missing."""
    s3 = S3.__new__(S3)
    s3.data_dir = temp_data_dir

    from_path, to_path = s3._prepare_paths(None, "src", None)
    assert from_path == Path("src")
    assert to_path == Path()

    from_path, to_path = s3._prepare_paths(None, None, "dst")
    assert from_path == Path()
    assert to_path == Path("dst")

    with pytest.raises(ValueError):
        s3._prepare_paths(None, None, None)
