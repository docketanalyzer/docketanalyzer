from pathlib import Path

import pytest
import simplejson as json


@pytest.fixture
def fixture_dir():
    """Path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_docket_id():
    """Load an example docket_id."""
    return "insd__1_24-cv-00524"


@pytest.fixture
def sample_docket_id2():
    """Another example docket_id."""
    return "nynd__8_20-mj-00487"


@pytest.fixture
def sample_docket_json(fixture_dir):
    """Load an example docket_json."""
    path = fixture_dir / "docket.json"
    return json.loads(path.read_text())


@pytest.fixture
def sample_docket_html(fixture_dir):
    """Load an example docket_html."""
    path = fixture_dir / "docket.html"
    return path.read_text()


@pytest.fixture
def sample_document_path(fixture_dir):
    """Load an example docket_html."""
    return fixture_dir / "document.pdf"


@pytest.fixture
def sample_attachment_path(fixture_dir):
    """Load an example docket_html."""
    return fixture_dir / "attachment.pdf"
