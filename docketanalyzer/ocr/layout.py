from pathlib import Path

from docketanalyzer import download_file

from .utils import box_overlap_pct, merge_boxes

LAYOUT_MODEL = None
LAYOUR_MODEL_PATH = (
    Path.home()
    / ".cache"
    / "docketanalyzer"
    / "ocr"
    / "doclayout_yolo_docstructbench_imgsz1280_2501.pt"
)
LAYOUR_MODEL_URL = "https://github.com/docketanalyzer/docketanalyzer/raw/refs/heads/main/data/doclayout_yolo_docstructbench_imgsz1280_2501.pt"


LAYOUT_CHOICES = {
    1: "text",
    0: "title",
    2: "abandon",
    3: "figure",
    4: "figure_caption",
    5: "table",
    6: "table_caption",
    7: "table_footnote",
    8: "isolate_formula",
    9: "formula_caption",
}


def merge_overlapping_blocks(blocks: list[dict]) -> list[dict]:
    """Merges overlapping layout blocks based on type priority.

    This function takes a list of detected layout blocks and merges any that overlap,
    keeping the type with the highest priority (lowest number in LAYOUT_CHOICES).

    Args:
        blocks: List of dictionaries, each with 'type' and 'bbox' keys.
               'bbox' is a tuple of (xmin, ymin, xmax, ymax).

    Returns:
        list[dict]: A new list with merged blocks, sorted by vertical
        position (y-coordinate) and then horizontal position (x-coordinate).
    """
    if not blocks:
        return []

    # Merged blocks with different types will get the type with the highest priority
    type_priority = {
        block_type: i for i, block_type in enumerate(LAYOUT_CHOICES.values())
    }

    unprocessed = [block.copy() for block in blocks]
    result = []

    while unprocessed:
        current = unprocessed.pop(0)
        current_bbox = current["bbox"]

        merged = True

        while merged:
            merged = False

            i = 0
            while i < len(unprocessed):
                other = unprocessed[i]
                other_bbox = other["bbox"]

                if box_overlap_pct(current_bbox, other_bbox) > 0.5:
                    current_priority = type_priority[current["type"]]
                    other_priority = type_priority[other["type"]]

                    if other_priority < current_priority:
                        current["type"] = other["type"]

                    current_bbox = merge_boxes(current_bbox, other_bbox)
                    current["bbox"] = current_bbox

                    unprocessed.pop(i)
                    merged = True
                else:
                    i += 1

        result.append(current)

    result.sort(key=lambda x: (x["bbox"][1], x["bbox"][0]))
    return result


def load_model() -> tuple["YOLOv10", str]:  # noqa: F821
    """Loads and initializes the document layout detection model.

    Returns:
        tuple[YOLOv10, str]: A tuple containing:
            - The initialized YOLOv10 model
            - The device string ('cpu' or 'cuda')
    """
    import torch
    from doclayout_yolo import YOLOv10

    global LAYOUT_MODEL

    device = "cpu" if not torch.cuda.is_available() else "cuda"

    if LAYOUT_MODEL is None:
        if not LAYOUR_MODEL_PATH.exists():
            LAYOUR_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            download_file(
                LAYOUR_MODEL_URL,
                LAYOUR_MODEL_PATH,
                description="Downloading layout model...",
            )
        LAYOUT_MODEL = YOLOv10(LAYOUR_MODEL_PATH, verbose=False)
        LAYOUT_MODEL.to(device)

    return LAYOUT_MODEL, device


def predict_layout(images: list, batch_size: int, dpi: int) -> list[list[dict]]:
    """Predicts document layout elements in a batch of images.

    This function processes a batch of images through the layout detection model
    to identify different document elements like text, tables, figures, etc.

    Args:
        images: List of images to process.
        batch_size: Number of images to process in each batch.
        dpi: Dots per inch (DPI) of the input images.

    Returns:
        list[list[dict]]: For each input image, a list of detected layout blocks,
        where each block is a dictionary with 'type' and 'bbox' keys.
    """
    model, _ = load_model()

    results = []
    for i in range(0, len(images), batch_size):
        batch = images[i : i + batch_size]
        preds = model(batch, verbose=False)

        for pred in preds:
            blocks = []
            for xyxy, cla in zip(
                pred.boxes.xyxy,
                pred.boxes.cls,
                strict=False,
            ):
                bbox = [int(p.item()) for p in xyxy]
                blocks.append(
                    {
                        "type": LAYOUT_CHOICES[int(cla.item())],
                        "bbox": [x * (72 / dpi) for x in bbox],
                    }
                )
            blocks = merge_overlapping_blocks(blocks)
            results.append(blocks)

    return results
