from typing import TYPE_CHECKING, Any

import fitz

if TYPE_CHECKING:
    from surya.detection import DetectionPredictor
    from surya.recognition import RecognitionPredictor


RECOGNITION_MODEL = None
DETECTION_MODEL = None


def load_model() -> tuple["RecognitionPredictor", "DetectionPredictor"]:
    """Loads and initializes the OCR models.

    Returns:
        tuple[RecognitionPredictor, DetectionPredictor]: A tuple containing:
            - The initialized RecognitionPredictor model
            - The initialized DetectionPredictor model
    """
    from surya.detection import DetectionPredictor
    from surya.recognition import RecognitionPredictor

    global RECOGNITION_MODEL, DETECTION_MODEL

    if RECOGNITION_MODEL is None:
        RECOGNITION_MODEL = RecognitionPredictor()
        RECOGNITION_MODEL.disable_tqdm = True
    if DETECTION_MODEL is None:
        DETECTION_MODEL = DetectionPredictor()
        DETECTION_MODEL.disable_tqdm = True

    return RECOGNITION_MODEL, DETECTION_MODEL


def extract_ocr_text(imgs: list[Any]) -> list[dict]:
    """Extracts text from an image using the OCR service.

    This function sends an image to the OCR service for processing and returns
    the extracted text and bounding boxes.

    Args:
        imgs: A list of input images.

    Returns:
        list[dict]: A list of dictionaries, each containing:
            - 'bbox': The bounding box coordinates [x1, y1, x2, y2]
            - 'content': The extracted text content
    """
    recognition_model, detection_model = load_model()

    preds = recognition_model(imgs, det_predictor=detection_model)

    results = []
    for pred in preds:
        results.append([])
        for line in pred.text_lines:
            results[-1].append({"bbox": line.bbox, "content": line.text})
    return results


def extract_native_text(page: fitz.Page) -> list[dict]:
    """Extracts text content and bounding boxes from a PDF page using native PDF text.

    This function extracts text directly from the PDF's internal structure
        rather than using OCR.

    Args:
        page: The pymupdf Page object to extract text from.

    Returns:
        list[dict]: A list of dictionaries, each containing:
            - 'bbox': The bounding box coordinates [x1, y1, x2, y2]
            - 'content': The text content of the line
    """
    blocks = page.get_text("dict")["blocks"]
    data = []
    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                content = "".join([span["text"] for span in line["spans"]])
                if content.strip():
                    data.append(
                        {
                            "bbox": line["bbox"],
                            "content": content,
                        }
                    )
    return data
