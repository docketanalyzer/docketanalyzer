import pytest

from docketanalyzer import Pacer, env, parse_docket_id


def is_valid_pdf(pdf_bytes):
    """Check if the bytes represent a valid PDF."""
    return pdf_bytes.startswith(b"%PDF-") and pdf_bytes.rstrip(b"\n").endswith(b"%%EOF")


@pytest.mark.cost
def test_pacer_credentials():
    """Test that PACER credentials are set in the environment variables."""
    key_check = bool(env.PACER_USERNAME and env.PACER_PASSWORD)
    assert key_check, "PACER credentials are not set in the environment variables"


@pytest.mark.cost
def test_purchase_docket(sample_docket_id, sample_docket_json):
    """Test purchasing a docket from PACER."""
    pacer = Pacer()
    docket_html, docket_json = pacer.purchase_docket(sample_docket_id)

    # Check that the docket number appears in the html
    _, docket_number = parse_docket_id(sample_docket_id)
    assert docket_number in docket_html

    # Compare some fields of the parsed json
    assert docket_json["pacer_case_id"] == sample_docket_json["pacer_case_id"]
    assert docket_json["court_id"] == sample_docket_json["court_id"]
    assert docket_json["docket_number"] == sample_docket_json["docket_number"]
    assert docket_json["case_name"] == sample_docket_json["case_name"]

    for i in range(5):
        entry = docket_json["docket_entries"][i]
        sample_entry = sample_docket_json["docket_entries"][i]
        assert entry["document_number"] == sample_entry["document_number"]
        assert entry["pacer_doc_id"] == sample_entry["pacer_doc_id"]
        assert entry["description"] == sample_entry["description"]


@pytest.mark.cost
def test_purchase_document(
    sample_docket_json, sample_document_path, sample_attachment_path
):
    """Test that downloaded document matches the fixture data."""
    pacer = Pacer()
    sample_pdf = sample_document_path.read_bytes()
    sample_attachment = sample_attachment_path.read_bytes()
    entry = sample_docket_json["docket_entries"][0]

    # Purchase document for the first entry
    pdf, _ = pacer.purchase_document(
        sample_docket_json["pacer_case_id"],
        entry["pacer_doc_id"],
        sample_docket_json["court_id"],
    )

    assert is_valid_pdf(pdf), "Downloaded document is not a valid PDF"
    assert abs(len(pdf) - len(sample_pdf)) < 10, "PDF doesn't match fixture data"

    # Purchase first attachment for the second entry
    pdf, _ = pacer.purchase_attachment(
        sample_docket_json["pacer_case_id"],
        entry["pacer_doc_id"],
        1,
        sample_docket_json["court_id"],
    )

    assert is_valid_pdf(pdf), "Downloaded document is not a valid PDF"
    assert abs(len(pdf) - len(sample_attachment)) < 10, "PDF doesn't match fixture data"
