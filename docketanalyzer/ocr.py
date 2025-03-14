try:
    import docketanalyzer_ocr  # noqa: F401
except ImportError as e:
    raise ImportError(
        "\n\nOCR extension not installed. "
        "Use `pip install docketanalyzer[ocr]` to install."
    ) from e
from docketanalyzer_ocr import pdf_document

__all__ = [
    "pdf_document",
]
