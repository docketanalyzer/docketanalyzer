from . import extension_required

with extension_required("ocr"):
    from docketanalyzer_ocr import (
        PDFDocument,
        box_overlap_pct,
        bulk_process_pdfs,
        extract_native_text,
        extract_ocr_text,
        load_pdf,
        merge_boxes,
        pdf_document,
        predict_layout,
    )


__all__ = [
    "PDFDocument",
    "box_overlap_pct",
    "bulk_process_pdfs",
    "extract_native_text",
    "extract_ocr_text",
    "load_pdf",
    "merge_boxes",
    "pdf_document",
    "predict_layout",
]
