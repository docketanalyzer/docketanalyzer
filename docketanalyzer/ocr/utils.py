import tempfile
from pathlib import Path

from docketanalyzer import load_clients


def load_pdf(
    file: bytes | None = None,
    s3_key: str | None = None,
    filename: str | None = None,
) -> tuple[bytes, str]:
    """Loads a PDF file either from binary content or S3.

    This function handles loading a PDF file from either binary or from an S3 bucket.
    It returns the binary content of the PDF file and the filename.

    Args:
        file: PDF file content as bytes. Defaults to None.
        s3_key: S3 key if the PDF should be fetched from S3. Defaults to None.
        filename: Optional filename to use. If not provided, will be derived
            from s3_key or set to a default.

    Returns:
        tuple[bytes, str]: A tuple containing:
            - The binary content of the PDF file
            - The filename of the PDF

    Raises:
        ValueError: If neither file nor s3_key is provided.
    """
    if file is None and s3_key is None:
        raise ValueError("Either file or s3_key must be provided")

    if filename is None:
        filename = Path(s3_key).name if s3_key else "document.pdf"

    # If we already have the file content, just return it
    if file is not None:
        return file, filename

    # Otherwise, we need to download from S3
    with tempfile.NamedTemporaryFile() as temp_file:
        temp_path = Path(temp_file.name)
        load_clients("s3").download(s3_key, str(temp_path))
        return temp_path.read_bytes(), filename


def box_overlap_pct(
    box1: tuple[float, float, float, float],
    box2: tuple[float, float, float, float],
    use_first_as_denominator: bool = False,
) -> float:
    """Calculates the percentage of overlap between two bounding boxes.

    The overlap percentage is calculated as the area of intersection divided by
    the smaller of the two box areas, resulting in a value between 0.0 and 1.0.

    Args:
        box1: Tuple of (xmin, ymin, xmax, ymax) for the first box.
        box2: Tuple of (xmin, ymin, xmax, ymax) for the second box.
        use_first_as_denominator: If True, use the first box's area as denominator.
                                  If False (default), use the smaller of the two areas.

    Returns:
        float: The overlap percentage (0.0 to 1.0)
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    # Calculate the area of each box
    area1 = (x1_max - x1_min) * (y1_max - y1_min)
    area2 = (x2_max - x2_min) * (y2_max - y2_min)

    # Calculate intersection coordinates
    x_overlap_min = max(x1_min, x2_min)
    x_overlap_max = min(x1_max, x2_max)
    y_overlap_min = max(y1_min, y2_min)
    y_overlap_max = min(y1_max, y2_max)

    # Check if there is an overlap
    if x_overlap_max <= x_overlap_min or y_overlap_max <= y_overlap_min:
        return 0.0

    # Calculate the area of the intersection
    intersection_area = (x_overlap_max - x_overlap_min) * (
        y_overlap_max - y_overlap_min
    )

    # Calculate the overlap percentage
    denominator = area1 if use_first_as_denominator else min(area1, area2)
    return intersection_area / denominator


def merge_boxes(
    box1: tuple[float, float, float, float], box2: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    """Merges two bounding boxes into one that encompasses both.

    Args:
        box1: Tuple of (xmin, ymin, xmax, ymax) for the first box.
        box2: Tuple of (xmin, ymin, xmax, ymax) for the second box.

    Returns:
        tuple[float, float, float, float]: A new bounding box that contains both
            input boxes.
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    merged_box = (
        min(x1_min, x2_min),
        min(y1_min, y2_min),
        max(x1_max, x2_max),
        max(y1_max, y2_max),
    )

    return merged_box
