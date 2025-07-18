import tempfile
from pathlib import Path

import pytest
import simplejson as json

from docketanalyzer import load_docket_index

FIXTURE_DIR = Path(__file__).parent / "fixtures"

TEST_DATA_DIR = FIXTURE_DIR / "docketanalyzer"

SAMPLE_DOCKET_ID1 = "insd__1_24-cv-00524"
SAMPLE_DOCKET_ID2 = "nynd__8_20-mj-00487"


@pytest.fixture
def index():
    """Load the docket index."""
    return load_docket_index(TEST_DATA_DIR)


@pytest.fixture
def model_dir():
    """Get a temporary run directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        model_dir = Path(temp_dir) / "test" / "model"
        model_dir.mkdir(parents=True, exist_ok=True)
        yield model_dir


@pytest.fixture
def sample_docket_id1():
    """Load an example docket_id."""
    return SAMPLE_DOCKET_ID1


@pytest.fixture
def sample_docket_id2():
    """Another example docket_id."""
    return SAMPLE_DOCKET_ID2


def get_recap_path(docket_id, mode):
    """Get a path to a recap file."""
    return FIXTURE_DIR / f"{docket_id}.recap.{mode}.json"
