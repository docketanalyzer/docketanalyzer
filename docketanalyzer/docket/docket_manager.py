import re
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
import peewee as pw
import simplejson as json

from docketanalyzer import json_default, parse_docket_id, to_int

if TYPE_CHECKING:
    from .docket_index import DocketIndex


class DocketManager:
    """Manager for an individual docket."""

    def __init__(self, docket_id: str, index: "DocketIndex"):
        """Initialize DocketManager."""
        self.docket_id = docket_id
        court, docket_number = parse_docket_id(docket_id)
        self.court = court
        self.docket_number = docket_number
        self.index = index
        self.dir = self.index.dir / self.docket_id
        self.docket_json_path = self.dir / "docket.json"

    # Docket data paths
    @property
    def docket_json(self):
        """Get the local path to the docket JSON file."""
        if self.docket_json_path.exists():
            return json.loads(self.docket_json_path.read_text())

    @property
    def docket_html_paths(self):
        """Get the local paths to the docket HTML files."""
        return list(self.dir.glob("pacer.*.html"))

    # Document data paths
    def parse_document_path(self, path):
        """Parse the document path to get the entry and attachment numbers."""
        path = Path(path)
        name = path.name.split(".")[-2]
        entry_number, attachment_number = name.split("_")
        entry_number, attachment_number = int(entry_number), int(attachment_number)
        attachment_number = attachment_number if attachment_number else None
        return entry_number, attachment_number

    def get_document_name(self, entry_number, attachment_number=None):
        """Get the name for a document based on entry and attachment numbers."""
        attachment_number = 0 if pd.isna(attachment_number) else attachment_number
        return f"{int(entry_number)}_{int(attachment_number)}"

    def get_pdf_path(self, entry_number, attachment_number=None):
        """Get path to document pdf based on entry and attachment numbers."""
        doc_name = self.get_document_name(entry_number, attachment_number)
        return self.dir / f"doc.pdf.{doc_name}.pdf"

    def get_ocr_path(self, entry_number, attachment_number=None):
        """Get path to document ocr data based on entry and attachment numbers."""
        doc_name = self.get_document_name(entry_number, attachment_number)
        return self.dir / f"doc.ocr.{doc_name}.json"

    @property
    def pdf_paths(self):
        """Get the local paths to the document PDF files."""
        return list(self.dir.glob("doc.pdf.*.pdf"))

    @property
    def ocr_paths(self):
        """Get the local paths to the document OCR JSON files."""
        return list(self.dir.glob("doc.ocr.*.json"))

    # OCR Utilities
    def apply_ocr(
        self, pdf_path: str | Path, overwrite: bool = False, **kwargs
    ) -> tuple[dict, Path]:
        """Apply OCR to a PDF document path and save the result."""
        entry_number, attachment_number = self.parse_document_path(pdf_path)
        ocr_path = self.get_ocr_path(entry_number, attachment_number)

        if not overwrite and ocr_path.exists():
            print(f"OCR file already exists: {ocr_path}")
            print("Pass `overwrite=True` to overwrite.")
            return False, ocr_path

        from docketanalyzer.ocr import pdf_document

        doc = pdf_document(pdf_path, **kwargs).process()
        doc.save(ocr_path)
        return doc.data, ocr_path

    # PACER Utilities
    def purchase_docket(self, update: bool = False, **kwargs: Any):
        """Purchase the docket from PACER.

        If a docket html already exists, we skip it unless `update` is True.
        Multiple htmls stored with versions as `pacer.{version}.html` etc.

        Args:
            update (bool): Whether to update the docket if it already exists.
            **kwargs: Additional arguments to pass to the Pacer purchase_docket method.
        """
        self.dir.mkdir(parents=True, exist_ok=True)
        docket_html_paths = list(self.docket_html_paths)
        if not update and docket_html_paths:
            print(f"Docket already purchased: {self.docket_id}")
            print("Pass `update=True` to purchase an updated version.")
            return False
        docket_html, _ = self.pacer.purchase_docket(self.docket_id, **kwargs)

        html_versions = [
            re.search(r"pacer\.(\d+)\.html", path.name) for path in docket_html_paths
        ]
        html_versions = [int(match.group(1)) for match in html_versions if match]
        new_version = max(html_versions) + 1 if html_versions else 0
        docket_html_path = self.dir / f"pacer.{new_version}.html"
        docket_html_path.write_text(docket_html)
        return True

    def parse_docket(self):
        """Parse the docket from the local files."""
        docket_html_paths = list(self.docket_html_paths)
        if not docket_html_paths:
            return False

        # TODO: Incorporate consolidation logic when multiple htmls
        docket_html_path = docket_html_paths[0]
        docket_html = docket_html_path.read_text()
        if not self.pacer.pacer_case_id_in_docket_html(docket_html):
            candidates = self.pacer.find_candidate_cases(self.docket_id)
            if candidates:
                pacer_case_id = candidates[0]["pacer_case_id"]
                docket_html = self.pacer.add_pacer_case_id_to_docket_html(
                    docket_html, pacer_case_id
                )
                docket_html_path.write_text(docket_html)
        docket_json = self.pacer.parse(docket_html, self.court)
        self.docket_json_path.write_text(
            json.dumps(docket_json, indent=2, default=json_default)
        )
        return True

    def purchase_document(
        self,
        entry_number,
        attachment_number=None,
        overwrite=False,
        suppress_errors=False,
    ):
        """Purchase a document from PACER."""
        pdf_path = self.get_pdf_path(entry_number, attachment_number)
        if not overwrite and pdf_path.exists():
            print(f"Document already purchased: {pdf_path}")
            print("Pass `overwrite=True` to purchase again.")
            return

        pacer_case_id = self.docket_json["pacer_case_id"]
        entry_json = self.get_entry_json(entry_number=entry_number)
        if entry_json is None or entry_json.get("pacer_doc_id") is None:
            print(f"Entry number {entry_number} not found in docket.")
            return False

        pacer_doc_id = entry_json["pacer_doc_id"]
        if attachment_number is None:
            pdf, status = self.pacer.purchase_document(
                pacer_case_id, pacer_doc_id, self.court
            )
        else:
            pdf, status = self.pacer.purchase_attachment(
                pacer_case_id, pacer_doc_id, attachment_number, court=self.court
            )
        success = status == "success"
        if not success:
            message = f"Failed to purchase document: {pdf_path}\nStatus: {status}"
            print(message)
            if not suppress_errors:
                raise ValueError(message)
            return False
        pdf_path.write_bytes(pdf)
        return success

    # Recap Utilities
    @property
    def recap_path(self):
        """Get the path to the recap data for this docket."""
        return self.dir / "recap.json"

    @property
    def recap_data(self):
        """Get the recap data for this docket."""
        if self.recap_path.exists():
            return json.loads(self.recap_path.read_text())

    def download_recap_data(self, overwrite: bool = False):
        """Download the recap data for this docket."""
        if not self.recap_path.exists() or overwrite:
            self.dir.mkdir(parents=True, exist_ok=True)
            r = self.recap.consolidated_docket(self.docket_id)
            results = json.dumps(r.results, indent=2)
            self.recap_path.write_text(results)
            return True
        print(f"Recap data already exists: {self.recap_path}")
        print("Pass `overwrite=True` to download again.")
        return False

    # S3
    @property
    def s3_key(self) -> str:
        """Get the S3 key for this docket."""
        return str(self.dir.relative_to(self.index.data_dir))

    def push(self, name=None, **kwargs):
        """Push the data for this docket to S3."""
        if name is not None:
            kwargs["exclude"] = "*"
            kwargs["include"] = name
        self.index.push(self.dir, **kwargs)

    def pull(self, name=None, **kwargs):
        """Pull the data for this docket from S3 to local."""
        if name is not None:
            kwargs["exclude"] = "*"
            kwargs["include"] = name
        self.index.pull(self.dir, **kwargs)

    # Additional utilities
    def add_to_index(self):
        """Add this docket to the index table."""
        with suppress(pw.IntegrityError):
            self.index.reset_cached_ids()
            self.table.insert({self.index.id_col: self.docket_id}).execute()

    def get_entry_json(self, row_number=None, entry_number=None):
        """Get the entry JSON for a given row or entry number."""
        if row_number is not None:
            return self.docket_json["docket_entries"][row_number]
        if entry_number is not None:
            for entry in self.docket_json["docket_entries"]:
                entry["document_number"] = to_int(entry["document_number"])
                if entry["document_number"] == entry_number:
                    return entry
            return None
        raise ValueError("Either row_number or entry_number must be provided.")

    def get_entry_attachment_json(self, row_number=None, entry_number=None):
        """Get the attachment JSON for a given row or entry number."""
        entry_json = self.get_entry_json(
            row_number=row_number, entry_number=entry_number
        )
        pacer_doc_id = entry_json["pacer_doc_id"]
        return self.pacer.get_attachments(pacer_doc_id, self.court)

    @property
    def row(self):
        """Get the row for this docket from the index table."""
        return self.table.get(self.table.docket_id == self.docket_id)

    @property
    def batch(self):
        """Get a batch of one for this docket."""
        return self.index.make_batch([self.docket_id])

    def __getattribute__(self, name: str):
        """Passthrough attributes from the index and batch."""
        index_attributes = ["db", "table", "s3", "pacer", "recap"]
        if name in index_attributes:
            return getattr(object.__getattribute__(self, "index"), name)

        return object.__getattribute__(self, name)

    def __repr__(self) -> str:
        """Return a string representation of the DocketManager."""
        return f"<DocketManager({self.docket_id})>"
