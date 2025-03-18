from . import extension_required

with extension_required("ocr"):
    from docketanalyzer_ocr import pdf_document


__all__ = [
    "pdf_document",
]
