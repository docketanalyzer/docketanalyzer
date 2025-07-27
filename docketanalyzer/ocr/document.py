import json
import tempfile
import uuid
from collections.abc import Generator, Iterator
from pathlib import Path

import fitz
import numpy as np
import regex as re
from PIL import Image
from tqdm import tqdm

from docketanalyzer import load_clients

from .layout import predict_layout
from .ocr import extract_native_text, extract_ocr_text
from .remote import RemoteClient
from .utils import box_overlap_pct, merge_boxes


def page_needs_ocr(
    page: "Page",
    layout: list[dict],
    min_overlap: float = 0.5,
) -> bool:
    """Determines whether a page needs OCR processing based on layout and text overlap.

    This function calculates the percentage of the page covered by layout blocks
    and compares it to the specified minimum overlap threshold.

    Args:
        page: The Page object to check.
        layout: The layout data for the page.
        min_overlap: The minimum overlap percentage to require for native text.

    Returns:
        bool: True if the page needs OCR processing, False otherwise.
    """
    page.extracted_text = extract_native_text(page.fitz)
    total_area = 0
    covered_area = 0
    for block in layout:
        x1_min, y1_min, x1_max, y1_max = block["bbox"]
        block_area = (x1_max - x1_min) * (y1_max - y1_min)
        block_coverage = 0
        for line in page.extracted_text:
            block_coverage += box_overlap_pct(
                block["bbox"],
                line["bbox"],
                use_first_as_denominator=True,
            )
        block_coverage = min(block_coverage, 1.0)
        total_area += block_area
        covered_area += block_area * block_coverage
    return covered_area / total_area < min_overlap


def consolidate_blocks(page: "Page", layout: list[list[dict]]):
    """Consolidates layout blocks with line data.

    This function merges layout blocks with extracted line data to create a list
    of consolidated blocks containing both layout and text information.
    Any lines not contained within a layout block are added as separate text blocks.
    """
    lines = page.extracted_text
    blocks = []
    for block in layout:
        block["lines"] = []
        drop_lines = []
        new_bbox = block["bbox"]
        for li, line in enumerate(lines):
            if box_overlap_pct(block["bbox"], line["bbox"]) > 0.5:
                block["lines"].append(line)
                drop_lines.append(li)
                new_bbox = merge_boxes(new_bbox, lines[li]["bbox"])
            block["bbox"] = new_bbox
        lines = [line for li, line in enumerate(lines) if li not in drop_lines]
        if len(block["lines"]) > 0:
            blocks.append(block)
    for line in lines:
        blocks.append(
            {
                "bbox": line["bbox"],
                "type": "text",
                "lines": [line],
            }
        )
    return blocks


def process_pages(
    pages: list["Page"],
    batch_size: int = 1,
    verbose=True,
) -> Generator["Page", None, None]:
    """Processes a list of pages and yields each processed page.

    Page order is not preserved for streaming efficiency.
    """
    needs_ocr = []

    for i in tqdm(list(range(0, len(pages), batch_size)), disable=not verbose):
        batch = pages[i : i + batch_size]

        layouts = predict_layout(
            [np.array(page.get_img(dpi=page.doc.dpi)) for page in batch],
            batch_size=batch_size,
            dpi=batch[0].doc.dpi,
        )

        for page, layout in zip(batch, layouts, strict=True):
            page.layout = layout
            if page_needs_ocr(page, page.layout):
                needs_ocr.append(page)
            else:
                page.set_blocks(consolidate_blocks(page, page.layout))
                yield page

        while len(needs_ocr) >= batch_size:
            ocr_batch = needs_ocr[:batch_size]
            needs_ocr = needs_ocr[batch_size:]
            ocr_data = extract_ocr_text([page.img for page in ocr_batch])
            for i, page in enumerate(ocr_batch):
                page.extracted_text = ocr_data[i]
                page.set_blocks(consolidate_blocks(page, page.layout))
                yield page

    if needs_ocr:
        ocr_data = extract_ocr_text([page.img for page in needs_ocr])
        for i, page in enumerate(needs_ocr):
            page.extracted_text = ocr_data[i]
            page.set_blocks(consolidate_blocks(page, page.layout))
            yield page


class DocumentComponent:
    """Base class for document components in the hierarchy.

    This is an abstract base class that defines the common interface and behavior
    for all document components (lines, blocks, pages, etc.) in the document hierarchy.

    Attributes:
        parent_attr: The attribute name that references the parent component.
        child_attr: The attribute name that references the child components.
        text_join: The string used to join text from child components.
    """

    parent_attr = None
    child_attr = None
    text_join = ""

    @property
    def parent(self):
        """Gets the parent component of this component.

        Returns:
            DocumentComponent: The parent component, or None if no parent exists.
        """
        if self.parent_attr is not None:
            return getattr(self, self.parent_attr, None)

    @property
    def children(self) -> list["DocumentComponent"]:
        """Gets the child components of this component.

        Returns:
            list[DocumentComponent]: A list of child components, or an empty list
                if no children exist.
        """
        if self.child_attr is not None:
            return getattr(self, self.child_attr, [])

    @property
    def page_num(self) -> int:
        """Gets the page number this component belongs to.

        Returns:
            int: The page number (0-indexed).
        """
        if isinstance(self, Page):
            return self.i
        return self.parent.page_num

    @property
    def doc(self) -> "PDFDocument":
        """Gets the document this component belongs to.

        Returns:
            PDFDocument: The parent document.
        """
        if isinstance(self, Page):
            return self._doc
        return self.parent.doc

    @property
    def text(self) -> str:
        """Gets the text content of this component.

        For Line components, returns the content directly.
        For other components, joins the text of all child components.

        Returns:
            str: The text content.
        """
        if isinstance(self, Line):
            return self.content
        return self.text_join.join([child.text for child in self.children])

    @property
    def id(self) -> str:
        """Gets a unique identifier for this component.

        Returns:
            str: A unique identifier string.
        """
        if isinstance(self, Page):
            return self.i
        return f"{self.parent.id}-{self.i}"

    def clip(
        self,
        bbox: tuple[float, float, float, float] | None = None,
        save: str | None = None,
    ):
        """Clips an image of this component from the parent page.

        Args:
            bbox: The bounding box to clip. If None, uses this component's bbox.
            save: Optional path to save the clipped image to.

        Returns:
            Image: The clipped image.
        """
        bbox = bbox or self.bbox
        return self.parent.clip(bbox, save)

    def __getitem__(self, idx: int) -> "DocumentComponent":
        """Gets a child component by index.

        Args:
            idx: The index of the child component.

        Returns:
            DocumentComponent: The child component at the specified index.
        """
        return self.children[idx]

    def __iter__(self) -> Iterator["DocumentComponent"]:
        """Iterates over child components.

        Yields:
            DocumentComponent: Each child component.
        """
        yield from self.children

    def __len__(self) -> int:
        """Gets the number of child components.

        Returns:
            int: The number of child components.
        """
        return len(self.children)


class Line(DocumentComponent):
    """Represents a line of text in a document.

    This is the lowest level component in the document hierarchy.

    Attributes:
        block: The parent block containing this line.
        i: The index of this line within its parent block.
        bbox: The bounding box coordinates [x1, y1, x2, y2].
        content: The text content of the line.
    """

    parent_attr = "block"

    def __init__(
        self,
        block: "Block",
        i: int,
        bbox: tuple[float, float, float, float],
        content: str,
    ):
        """Initializes a new Line component.

        Args:
            block: The parent block containing this line.
            i: The index of this line within its parent block.
            bbox: The bounding box coordinates [x1, y1, x2, y2].
            content: The text content of the line.
        """
        self.block = block
        self.i = i
        self.bbox = bbox
        self.content = content

    @property
    def data(self) -> dict:
        """Gets a dictionary representation of this line.

        Returns:
            dict: A dictionary containing the line's data.
        """
        return {
            "i": self.i,
            "bbox": self.bbox,
            "content": self.content,
        }


class Block(DocumentComponent):
    """Represents a block of text in a document.

    A block contains one or more lines of text.

    Attributes:
        page: The parent page containing this block.
        i: The index of this block within its parent page.
        bbox: The bounding box coordinates [x1, y1, x2, y2].
        block_type: The type of block (e.g., 'text', 'image', etc.).
        lines: The list of Line components in this block.
    """

    parent_attr = "page"
    child_attr = "lines"
    text_join = "\n"

    def __init__(
        self,
        page: "Page",
        i: int,
        bbox: tuple[float, float, float, float],
        block_type: str = "text",
        lines: list[dict] | None = None,
    ):
        """Initializes a new Block component.

        Args:
            page: The parent page containing this block.
            i: The index of this block within its parent page.
            bbox: The bounding box coordinates [x1, y1, x2, y2].
            block_type: The type of block. Defaults to 'text'.
            lines: A list of line data to initialize with.
        """
        self.page = page
        self.i = i
        self.bbox = bbox
        self.block_type = block_type
        self.lines = []
        if lines is not None:
            self.lines = [
                Line(self, i, line["bbox"], line["content"])
                for i, line in enumerate(lines)
            ]

    @property
    def data(self) -> dict:
        """Gets a dictionary representation of this block.

        Returns:
            dict: A dictionary containing the block's data.
        """
        return {
            "i": self.i,
            "bbox": self.bbox,
            "type": self.block_type,
            "lines": [line.data for line in self.lines],
        }


class Page(DocumentComponent):
    """Represents a page in a document.

    A page contains one or more blocks of content.

    Attributes:
        _doc: The parent document containing this page.
        i: The index of this page within the document.
        blocks: The list of Block components on this page.
        img: The image representation of the page (set during processing).
        extracted_text: The extracted text data (set during processing).
        needs_ocr: Whether this page needs OCR processing.
    """

    parent_attr = "doc"
    child_attr = "blocks"
    text_join = "\n\n"

    def __init__(self, doc: "PDFDocument", i: int, blocks: list[dict] | None = None):
        """Initializes a new Page component.

        Args:
            doc: The parent document containing this page.
            i: The index of this page within the document.
            blocks: A list of block data to initialize with.
        """
        self._doc = doc
        self.i = i
        self.blocks = []
        self.extracted_text = None
        self.layout = None
        if blocks is not None:
            self.set_blocks(blocks)

    def get_img(self, dpi: int | None = None) -> Image.Image:
        """Gets the image representation of this page."""
        if dpi is not None:
            mat = fitz.Matrix(self.doc.dpi / 72, self.doc.dpi / 72)
            pm = self.fitz.get_pixmap(matrix=mat, alpha=False)
            if pm.width > 4500 or pm.height > 4500:
                pm = self.fitz.get_pixmap(alpha=False)
        else:
            pm = self.fitz.get_pixmap(alpha=False)
        return Image.frombytes("RGB", (pm.width, pm.height), pm.samples)

    @property
    def img(self) -> Image.Image:
        """Gets the image representation of this page."""
        return self.get_img()

    @property
    def fitz(self) -> fitz.Page:
        """Gets the underlying PyMuPDF page object.

        Returns:
            fitz.Page: The PyMuPDF page object.
        """
        return self._doc.doc[self.i]

    def draw(self, bbox: tuple[float, float, float, float], **kwargs) -> None:
        """Draws a rectangle on the page."""
        bbox = [x for x in bbox]
        rect = fitz.Rect(*bbox)
        self.fitz.draw_rect(rect, **kwargs)

    def set_blocks(self, blocks: list[dict]) -> None:
        """Sets the blocks for this page.

        Args:
            blocks: A list of block data to set.
        """
        blocks = sorted(blocks, key=lambda x: x["bbox"][1])
        self.blocks = [
            Block(
                self,
                i,
                block.get("bbox"),
                block.get("type", "text"),
                block.get("lines", []),
            )
            for i, block in enumerate(blocks)
        ]

    def clip(
        self,
        bbox: tuple[float, float, float, float] | None = None,
        save: str | None = None,
    ) -> Image.Image:
        """Clips an image from this page.

        Args:
            bbox: The bounding box to clip. If None, uses the entire page.
            save: Optional path to save the clipped image to.

        Returns:
            Image.Image: The clipped image.
        """
        if self.img is None:
            return None

        x1, y1, x2, y2 = bbox or (0, 0, self.img.shape[1], self.img.shape[0])
        clip = self.img[int(y1) : int(y2), int(x1) : int(x2)]

        if save:
            Image.fromarray(clip).save(save)

        return clip

    @property
    def data(self) -> dict:
        """Gets a dictionary representation of this page.

        Returns:
            dict: A dictionary containing the page's data.
        """
        return {
            "i": self.i,
            "blocks": [block.data for block in self.blocks],
        }


class PDFDocument:
    """Represents a PDF document.

    This class handles loading, processing, and extracting text from PDF
        documents. It manages the document hierarchy (pages, blocks, lines)
        and handles OCR when needed.

    Attributes:
        doc: The underlying PyMuPDF document.
        filename: The name of the PDF file.
        dpi: The resolution to use when rendering pages for OCR.
        pages: The list of Page components in the document.
        remote: Whether to use remote processing via RemoteClient.
    """

    def __init__(
        self,
        file_or_path: bytes | str | Path,
        filename: str | None = None,
        dpi: int = 200,
        use_s3: bool = True,
        remote: bool = False,
        api_key: str | None = None,
        endpoint_url: str | None = None,
    ):
        """Initializes a new PDFDocument.

        Args:
            file_or_path: The PDF file content as bytes, or a path to the PDF file.
            filename: Optional name for the PDF file.
            dpi: The resolution to use when rendering pages for OCR. Defaults to 200.
            use_s3: Whether to upload the PDF to S3 for remote processing.
                Defaults to True.
            remote: Whether to use remote processing via RemoteClient.
                Defaults to False.
            api_key: Optional API key for remote processing.
            endpoint_url: Optional full endpoint URL for remote processing.
        """
        if isinstance(file_or_path, bytes):
            self.doc = fitz.open("pdf", file_or_path)
            self.pdf_bytes = file_or_path
            self.pdf_path = None
            self.filename = filename or "document.pdf"
        else:
            self.doc = fitz.open(file_or_path)
            self.pdf_bytes = self.doc.tobytes()
            self.pdf_path = Path(file_or_path).resolve()
            self.filename = filename or self.pdf_path.name
        self.dpi = dpi
        self.remote = remote
        self.pages = [Page(self, i) for i in range(len(self.doc))]
        self.remote_client = RemoteClient(api_key=api_key, endpoint_url=endpoint_url)
        self.use_s3 = use_s3
        self.s3 = load_clients("s3")
        self.s3_available = self.s3.status()
        self.s3_key = (
            None if not self.s3_available else f"tmp/{uuid.uuid4()}_{self.filename}"
        )

    def stream(self, batch_size: int = 1) -> Generator[Page, None, None]:
        """Processes the document page by page and yields each processed page.

        If remote=True, uses the RemoteClient for processing.

        Args:
            batch_size: Number of pages to process in each batch. Defaults to 1.

        Yields:
            Page: Each processed page.
        """
        if self.remote:
            s3_key, file = None, None
            try:
                if self.use_s3 and self.s3_available:
                    if self.pdf_path is not None:
                        self.s3.upload(self.pdf_path, self.s3_key)
                    else:
                        with tempfile.NamedTemporaryFile() as f:
                            f.write(self.pdf_bytes)
                            self.s3.upload(f.name, self.s3_key)
                    s3_key = self.s3_key
                else:
                    file = self.pdf_bytes

                for result in self.remote_client(
                    file=file,
                    s3_key=s3_key,
                    filename=self.filename,
                    batch_size=batch_size,
                ):
                    if "stream" in result:
                        for stream_item in result["stream"]:
                            if (
                                "output" in stream_item
                                and "page" in stream_item["output"]
                            ):
                                page_data = stream_item["output"]["page"]
                                page_idx = page_data.get("i", 0)

                                if page_idx < len(self.pages):
                                    self.pages[page_idx].set_blocks(
                                        page_data.get("blocks", [])
                                    )
                                    yield self.pages[page_idx]

                    status = result.get("status")
                    if status == "COMPLETED":
                        break
                    elif status in ["FAILED", "CANCELLED"]:
                        raise Exception(result)
            finally:
                if s3_key is not None:
                    self.s3.delete(self.s3_key)
        else:
            yield from process_pages(self.pages, batch_size=batch_size)

    def process(self, batch_size: int = 1) -> "PDFDocument":
        """Processes the entire document at once.

        This just runs stream in a loop and returns the document when done.

        Args:
            batch_size: Number of pages to process in each batch. Defaults to 1.

        Returns:
            PDFDocument: The processed document (self).
        """
        for _ in self.stream(batch_size=batch_size):
            pass
        return self

    def postprocess_court_doc(self) -> "PDFDocument":
        """Post-processes the document to ignore certain blocks.

        This method uses a few heuristics to identify and certain blocks to ignore
        """
        heading_pattern = r"^.{0,50}ase \d+[-:]\d+[-\w]+.{1,200}\s+Page \d+ of \d+"
        for page in self:
            for block in page:
                if (
                    re.match(heading_pattern, block.text, flags=re.IGNORECASE)
                    or block.text.strip().isdigit()
                    or (
                        block.block_type == "abandon"
                        and not any(len(line.text) > 4 for line in block)
                    )
                ):
                    block.block_type = "ignore"
        return self

    @property
    def data(self) -> dict:
        """Gets a dictionary representation of this document.

        Returns:
            dict: A dictionary containing the document's data.
        """
        return {
            "filename": self.filename,
            "pages": [page.data for page in self.pages],
        }

    def save(self, path: str | Path) -> None:
        """Saves the document data to a JSON file.

        Args:
            path: The path to save the JSON file to.
        """
        Path(path).write_text(json.dumps(self.data, indent=2))

    def load(self, path_or_data: str | Path | dict) -> "PDFDocument":
        """Loads document data from a JSON file or dictionary.

        Args:
            path_or_data: Either a path to a JSON file or a dictionary of document data.

        Returns:
            PDFDocument: The loaded document (self).
        """
        if isinstance(path_or_data, str | Path):
            path = Path(path_or_data)
            data = json.loads(path.read_text())
        else:
            data = path_or_data

        self.filename = data.get("filename", self.filename)
        for i, page_data in enumerate(data.get("pages", [])):
            if i < len(self.pages):
                self.pages[i].set_blocks(page_data.get("blocks", []))

        return self

    def close(self) -> None:
        """Closes the underlying PyMuPDF document."""
        self.doc.close()

    def __getitem__(self, idx: int) -> Page:
        """Gets a page by index.

        Args:
            idx: The index of the page.

        Returns:
            Page: The page at the specified index.
        """
        return self.pages[idx]

    def __iter__(self) -> Iterator[Page]:
        """Iterates over pages in the document.

        Yields:
            Page: Each page in the document.
        """
        yield from self.pages

    def __len__(self) -> int:
        """Gets the number of pages in the document.

        Returns:
            int: The number of pages.
        """
        return len(self.pages)


def pdf_document(
    file_or_path: bytes | str | Path,
    filename: str | None = None,
    dpi: int = 200,
    use_s3: bool = True,
    remote: bool = False,
    api_key: str | None = None,
    endpoint_url: str | None = None,
    load: str | Path | dict | None = None,
) -> PDFDocument:
    """Processes a PDF file for text extraction.

    This is the main entry point for processing PDF documents. It creates a PDFDocument
    instance, optionally loads existing data, and processes the document if requested.

    Args:
        file_or_path: The PDF file content as bytes, or a path to the PDF file.
        filename: Optional name for the PDF file.
        dpi: The resolution to use when rendering pages for OCR. Defaults to 200.
        use_s3: Whether to upload the PDF to S3 for remote processing. Defaults
            to True.
        remote: Whether to use remote processing via RemoteClient. Defaults to False.
        api_key: Optional API key for remote processing.
        endpoint_url: Optional full endpoint URL for remote processing.
        load: Optional path to a JSON file or dictionary with existing document
            data to load.

    Returns:
        PDFDocument: The created (and possibly processed) document.
    """
    doc = PDFDocument(
        file_or_path,
        filename=filename,
        dpi=dpi,
        use_s3=use_s3,
        remote=remote,
        api_key=api_key,
        endpoint_url=endpoint_url,
    )

    if load is not None:
        doc.load(load)

    return doc


def bulk_process_pdfs(
    docs: list[PDFDocument | dict | Path | str], batch_size: int
) -> list[PDFDocument]:
    """Processes a list of PDF documents in bulk.

    Args:
        docs: A list of PDFDocument instances to process (or paths or init args).
        batch_size: Number of pages to process in each batch. Defaults to 1.

    Returns:
        list[PDFDocument]: A list of processed PDFDocument instances.
    """
    all_docs = []
    for doc in docs:
        if isinstance(doc, str | Path):
            doc = pdf_document(doc)
        elif isinstance(doc, dict):
            doc = pdf_document(**doc)
        all_docs.append(doc)
    pages = [page for doc in all_docs for page in doc]
    for _ in process_pages(pages, batch_size=batch_size):
        pass
    return all_docs
