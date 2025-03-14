import pytest
import simplejson as json


@pytest.fixture
def sample_docket_id():
    """Load an example docket_id."""
    return "insd__1_24-cv-00524"


@pytest.fixture
def sample_docket_json(fixture_dir):
    """Load an example docket_json."""
    path = fixture_dir / "docket" / "docket.json"
    return json.loads(path.read_text())


@pytest.fixture
def sample_docket_html(fixture_dir):
    """Load an example docket_html."""
    path = fixture_dir / "docket" / "docket.html"
    return path.read_text()


@pytest.fixture
def sample_document_path(fixture_dir):
    """Load an example docket_html."""
    return fixture_dir / "docket" / "document.pdf"


@pytest.fixture
def sample_attachment_path(fixture_dir):
    """Load an example docket_html."""
    return fixture_dir / "docket" / "attachment.pdf"
