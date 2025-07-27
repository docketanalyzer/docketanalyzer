import pytest

from docketanalyzer import env, parse_docket_id


def is_valid_pdf(pdf_bytes):
    """Check if the bytes represent a valid PDF."""
    return pdf_bytes.startswith(b"%PDF-") and pdf_bytes.rstrip(b"\n").endswith(b"%%EOF")


@pytest.mark.cost
def test_pacer_credentials():
    """Test that PACER credentials are set in the environment variables."""
    key_check = bool(env.PACER_USERNAME and env.PACER_PASSWORD)
    assert key_check, "PACER credentials are not set in the environment variables"


@pytest.mark.cost
def test_purchase_docket(index, sample_docket_id1):
    """Test purchasing a docket from PACER."""
    from docketanalyzer.pacer import Pacer

    manager = index[sample_docket_id1]

    pacer = Pacer()
    docket_html, docket_json = pacer.purchase_docket(sample_docket_id1)

    # Check that the docket number appears in the html
    _, docket_number = parse_docket_id(sample_docket_id1)
    assert docket_number in docket_html

    cached_docket_json = manager.docket_json

    # Compare some fields of the parsed json
    assert docket_json["pacer_case_id"] == cached_docket_json["pacer_case_id"]
    assert docket_json["court_id"] == cached_docket_json["court_id"]
    assert docket_json["docket_number"] == cached_docket_json["docket_number"]
    assert docket_json["case_name"] == cached_docket_json["case_name"]

    for i in range(5):
        entry = docket_json["docket_entries"][i]
        cached_entry = cached_docket_json["docket_entries"][i]
        assert entry["document_number"] == cached_entry["document_number"]
        assert entry["pacer_doc_id"] == cached_entry["pacer_doc_id"]
        assert entry["description"] == cached_entry["description"]


@pytest.mark.cost
def test_purchase_document(index, sample_docket_id1):
    """Test that downloaded document matches the fixture data."""
    from docketanalyzer.pacer import Pacer

    entry_number, attachment_number = 1, 1
    manager = index[sample_docket_id1]
    cached_docket_json = manager.docket_json
    cached_document_path = manager.get_pdf_path(entry_number)
    cached_attachment_path = manager.get_pdf_path(entry_number, attachment_number)
    entry = manager.get_entry_json(entry_number=entry_number)

    pacer = Pacer()

    # Purchase document for the first entry
    cached_pdf = cached_document_path.read_bytes()
    pdf, status = pacer.purchase_document(
        cached_docket_json["pacer_case_id"],
        entry["pacer_doc_id"],
        cached_docket_json["court_id"],
    )

    assert status == "success", "Failed to purchase document"
    assert is_valid_pdf(pdf), "Downloaded document is not a valid PDF"
    assert abs(len(pdf) - len(cached_pdf)) < 10, "PDF doesn't match fixture data"

    # Purchase first attachment for the first entry
    cached_attachment = cached_attachment_path.read_bytes()

    pdf, status = pacer.purchase_attachment(
        cached_docket_json["pacer_case_id"],
        entry["pacer_doc_id"],
        attachment_number,
        cached_docket_json["court_id"],
    )

    assert status == "success", "Failed to purchase attachment"
    assert is_valid_pdf(pdf), "Downloaded document is not a valid PDF"
    assert abs(len(pdf) - len(cached_attachment)) < 10, "PDF doesn't match fixture data"
