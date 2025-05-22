import shutil
from contextlib import suppress
from datetime import datetime
from pathlib import Path

import botocore
import pandas as pd
import peewee as pw
import pytest

from docketanalyzer import (
    DatabaseModel,
    env,
    load_elastic,
    load_psql,
    load_redis,
    load_s3,
)
from docketanalyzer.services.s3 import S3


@pytest.fixture(scope="session")
def dummy_data():
    """Create dummy data for testing."""
    data = pd.DataFrame(
        {
            "email": ["alice@example.com", "bob@example.com"],
            "age": [30, 25],
            "registration_date": [datetime(2020, 1, 1), datetime(2021, 1, 15)],
        }
    )

    return data


@pytest.fixture(scope="session")
def db_with_test_table():
    """Create a test table in the database."""
    db = load_psql()

    with suppress(KeyError):
        db.drop_table("test_schemaless", confirm=False)

    db.create_table("test_schemaless")

    yield db

    db.drop_table("test_schemaless", confirm=False)
    db.close()


@pytest.fixture(scope="session")
def table_schema():
    """Create a test table schema."""

    class TestTable(DatabaseModel):
        email = pw.TextField(unique=True)
        age = pw.IntegerField()
        registration_date = pw.DateTimeField()

        class Meta:
            table_name = "test_standard"

    db = load_psql()

    with suppress(KeyError):
        db.drop_table("test_standard", confirm=False)

    yield TestTable

    db.reload()
    db.drop_table("test_standard", confirm=False)
    db.close()


@pytest.fixture(scope="session")
def temp_data_dir():
    """Create a temp directory in DATA_DIR for S3 tests."""
    temp_dir = env.DATA_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    yield temp_dir

    shutil.rmtree(temp_dir)


@pytest.mark.local
def test_elastic_connection():
    """Test the Elasticsearch service."""
    key_check = bool(env.ELASTIC_URL)
    assert key_check, "ELASTIC_URL is not set"

    es = load_elastic()

    assert es.ping(), "Elasticsearch could not connect"


@pytest.mark.local
def test_psql_connection():
    """Test the Postgres service."""
    key_check = bool(env.POSTGRES_URL)
    assert key_check, "POSTGRES_URL is not set"

    db = load_psql()

    assert db.status(), "Postgres could not connect"


@pytest.mark.local
def test_psql_schemaless_table(dummy_data, db_with_test_table):
    """Test the schemaless table functionality."""
    db = db_with_test_table
    table = db.t.test_schemaless

    # Add columns to the table and reload
    table.add_column("email", column_type="TextField", unique=True)
    table.add_column("age", column_type="IntegerField")
    table.add_column("registration_date", column_type="DateTimeField")
    table = db.t.test_schemaless

    # Add data to the table
    table.add_data(dummy_data)

    # Make sure that adding duplicate data raises an IntegrityError
    error = False
    try:
        table.add_data(dummy_data)
    except pw.IntegrityError:
        error = True
    assert error

    # Test pandas functionality
    data = table.pandas()

    assert len(data) == 2

    # Test sample functionality
    data = table.sample(1).pandas()

    assert len(data) == 1

    # Test delete functionality
    table.delete().where(table.email == "bob@example.com").execute()

    data = table.pandas("email")["email"].tolist()

    assert len(data) == 1
    assert data[0] == "alice@example.com"


@pytest.mark.local
def test_psql_standard_table(dummy_data, table_schema):
    """Test the standard table functionality."""
    test_table = table_schema
    db = load_psql()

    # Register and create the table
    db.register_model(test_table)
    db.create_table(test_table)
    table = db.t.test_standard

    # Add data to the table using copy
    table.add_data(dummy_data, copy=True)

    data = table.pandas()

    assert len(data) == 2
    assert data["registration_date"].dtype == "datetime64[ns]"
    assert data["age"].dtype == "int64"
    assert data["email"].dtype == "object"

    # Test batching functionality
    n = 0
    for batch in table.batch(1):
        assert len(batch) == 1
        n += 1
    assert n == 2

    db.close()


@pytest.mark.local
def test_redis_connection():
    """Test the Redis service."""
    key_check = bool(env.REDIS_URL)
    assert key_check, "REDIS_URL is not set"

    redis = load_redis()

    assert redis.ping(), "Redis could not connect"


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

    s3 = load_s3()

    assert s3.status(), "S3 could not connect"


def test_s3_upload_and_delete(temp_data_dir, dummy_data):
    """Test the S3 upload and delete functionality."""
    s3 = load_s3()

    # Create a temporary file
    path = temp_data_dir / "test.csv"
    dummy_data.to_csv(path, index=False)

    # Upload the file to S3
    s3_key = s3.upload(path)

    assert s3_key is not None

    path.unlink()

    assert not path.exists()

    # Download the file from S3
    s3.download(s3_key)

    assert path.exists()

    # Delete the file from S3
    s3.delete(s3_key)

    error = False
    try:
        s3.download(s3_key)
    except botocore.exceptions.ClientError:
        error = True
    assert error


def test_s3_push_and_pull(temp_data_dir, dummy_data):
    """Test the S3 push and pull functionality."""
    s3 = load_s3()

    # Create a temporary file
    path = temp_data_dir / "test.csv"
    dummy_data.to_csv(path, index=False)

    # Push the file to S3
    s3.push(temp_data_dir)
    path.unlink()

    assert not path.exists()

    # Pull the file from S3
    s3.pull(temp_data_dir)

    assert path.exists()

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
