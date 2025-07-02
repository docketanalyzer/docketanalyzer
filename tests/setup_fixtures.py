import simplejson as json
from conftest import (
    SAMPLE_DOCKET_ID1,
    SAMPLE_DOCKET_ID2,
    get_docket_html_path,
    get_docket_json_path,
    get_document_pdf_path,
    get_recap_path,
)

from docketanalyzer import json_default
from docketanalyzer.pacer import Pacer, RecapAPI

if __name__ == "__main__":
    overwrite_pacer = False
    overwrite_recap = False

    pacer = Pacer()
    recap = RecapAPI()
    for docket_id in [SAMPLE_DOCKET_ID1, SAMPLE_DOCKET_ID2]:
        docket_json_path = get_docket_json_path(docket_id)
        docket_html_path = get_docket_html_path(docket_id)
        if (
            not docket_json_path.exists()
            or not docket_html_path.exists()
            or overwrite_pacer
        ):
            docket_html, docket_json = pacer.purchase_docket(docket_id)
            docket_json_path.write_text(
                json.dumps(docket_json, indent=2, default=json_default)
            )
            docket_html_path.write_text(docket_html)

        docket_json = json.loads(docket_json_path.read_text())

        row_number = 0
        entry = docket_json["docket_entries"][row_number]
        entry_number = entry["document_number"]
        attachment_number = 1
        sample_document_path = get_document_pdf_path(docket_id, entry_number)
        sample_attachment_path = get_document_pdf_path(
            docket_id, entry_number, attachment_number
        )

        if not sample_document_path.exists() or overwrite_pacer:
            pdf, _ = pacer.purchase_document(
                docket_json["pacer_case_id"],
                entry["pacer_doc_id"],
                docket_json["court_id"],
            )
            sample_document_path.write_bytes(pdf)

        if docket_id == SAMPLE_DOCKET_ID1 and (
            not sample_attachment_path.exists() or overwrite_pacer
        ):
            pdf, _ = pacer.purchase_attachment(
                docket_json["pacer_case_id"],
                entry["pacer_doc_id"],
                attachment_number,
                docket_json["court_id"],
            )
            sample_attachment_path.write_bytes(pdf)

        endpoints = [
            ("docket", recap.dockets),
            ("entries", recap.entries),
            ("parties", recap.parties),
            ("attorneys", recap.attorneys),
            ("consolidated", recap.consolidated_docket),
        ]

        for endpoint, func in endpoints:
            recap_path = get_recap_path(docket_id, endpoint)
            if not recap_path.exists() or overwrite_recap:
                recap_json = func(docket_id).results
                recap_path.write_text(
                    json.dumps(recap_json, indent=2, default=json_default)
                )
