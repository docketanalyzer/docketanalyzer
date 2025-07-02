from pathlib import Path

import pytest
import simplejson as json

FIXTURE_DIR = Path(__file__).parent / "fixtures"

SAMPLE_DOCKET_ID1 = "insd__1_24-cv-00524"
SAMPLE_DOCKET_ID2 = "nynd__8_20-mj-00487"


@pytest.fixture
def fixture_dir():
    """Path to the fixtures directory."""
    return FIXTURE_DIR


@pytest.fixture
def sample_docket_id1():
    """Load an example docket_id."""
    return SAMPLE_DOCKET_ID1


@pytest.fixture
def sample_docket_id2():
    """Another example docket_id."""
    return SAMPLE_DOCKET_ID2


def get_docket_json_path(docket_id):
    """Get a path to a docket json file."""
    return FIXTURE_DIR / f"{docket_id}.docket.json"


def get_docket_json(docket_id):
    """Get a docket json."""
    return json.loads(get_docket_json_path(docket_id).read_text())


def get_docket_html_path(docket_id):
    """Get a path to a docket html file."""
    return FIXTURE_DIR / f"{docket_id}.docket.html"


def get_docket_html(docket_id):
    """Get a docket html."""
    return get_docket_html_path(docket_id).read_text()


def get_document_pdf_path(
    docket_id, entry_number, attachment_number=None, ocr_path=False
):
    """Get a path to a document pdf file."""
    suffix = ".json" if ocr_path else ".pdf"
    if attachment_number is None:
        return FIXTURE_DIR / f"{docket_id}.doc.{entry_number}.0{suffix}"
    else:
        return (
            FIXTURE_DIR / f"{docket_id}.doc.{entry_number}.{attachment_number}{suffix}"
        )


def get_document_ocr_path(docket_id, entry_number, attachment_number=None):
    """Get a path to a document ocr file."""
    return get_document_pdf_path(
        docket_id, entry_number, attachment_number, ocr_path=True
    )


def get_recap_path(docket_id, mode):
    """Get a path to a recap file."""
    return FIXTURE_DIR / f"{docket_id}.recap.{mode}.json"
