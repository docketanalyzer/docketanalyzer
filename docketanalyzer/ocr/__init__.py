from docketanalyzer import extension_required

with extension_required("ocr"):
    from .document import PDFDocument, pdf_document, bulk_process_pdfs
    from .layout import predict_layout
    from .ocr import extract_ocr_text, extract_native_text
    from .utils import load_pdf, merge_boxes, box_overlap_pct


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
