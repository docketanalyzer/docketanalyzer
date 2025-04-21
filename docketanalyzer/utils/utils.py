import hashlib
import secrets
import string
from contextlib import suppress
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
import simplejson as json
from dateutil.parser import ParserError
from pandas.errors import OutOfBoundsDatetime
from tqdm import tqdm

BASE_DIR = Path(__file__).parent.parent.resolve()
CONFIG_DIR = Path.home() / ".cache" / "docketanalyzer"


EXTENSIONS = [
    "pacer",
    "ocr",
]


class extension_required:
    """Context manager extension imports."""

    def __init__(self, extension: str):
        """Initialize context manager."""
        self.extension = extension

    def __enter__(self):
        """Enter the context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handle import errors with helpful messages."""
        if exc_type is not None and issubclass(exc_type, ImportError):
            raise ImportError(
                f"\n\n{self.extension} extension not installed. "
                f"Use `pip install 'docketanalyzer[{self.extension}]'` to install."
            ) from exc_val

        return False


def parse_docket_id(docket_id: str) -> tuple[str, str]:
    """Parse a docket ID into a court and docket number."""
    court, docket_number = docket_id.split("__")
    docket_number = docket_number.replace("_", ":")
    return court, docket_number


def construct_docket_id(court: str, docket_number: str) -> str:
    """Construct a docket ID from a court and docket number."""
    formatted_number = docket_number.replace(":", "_")
    return f"{court}__{formatted_number}"


def json_default(obj: Any) -> Any:
    """Default JSON serializer for datetime and date objects."""
    if isinstance(obj, datetime | date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def notabs(text: str) -> str:
    """Remove leading/trailing whitespace on each line."""
    return "\n".join([x.strip() for x in text.split("\n")]).strip()


def download_file(url: str, path: str | Path, description: str = "Downloading"):
    """Download file from URL to local path with progress bar."""
    path = Path(path)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get("content-length", 0))

    with (
        path.open("wb") as file,
        tqdm(
            desc=description,
            total=total_size,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as progress,
    ):
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress.update(size)


class timeit:
    """Context manager for timing things.

    Usage:
    with timeit("Task"):
        # do something
        do_something()

    This will print the time taken to execute the block of code.
    """

    def __init__(self, description: str = "Task"):
        """Initialize the timeit context manager with a description."""
        self.description = description
        self.start = None

    def __enter__(self):
        """Start the timer."""
        self.start = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Print the execution time."""
        end = datetime.now()
        execution_time = (end - self.start).total_seconds()
        print(f"{self.description} took {execution_time:.4f} seconds")


def generate_hash(data: Any, salt: str | None = None, length: int | None = None) -> str:
    """Generate a hash for some data with optional salt."""
    data = json.dumps({"data": data}, sort_keys=True, default=json_default)
    if salt:
        data += salt
    hash = hashlib.sha256(data.encode()).hexdigest()
    if length:
        hash = hash[:length]
    return hash


def generate_code(length: int = 16) -> str:
    """Generate a random code of specified length."""
    abc = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(abc) for _ in range(length))


def pd_save_or_append(data: pd.DataFrame, path: str | Path, **kwargs):
    """Save or append a DataFrame to a CSV file."""
    path = Path(path)
    if path.exists():
        data.to_csv(path, mode="a", header=False, index=False, **kwargs)
    else:
        data.to_csv(path, index=False, **kwargs)


def datetime_utcnow() -> datetime:
    """Get the current UTC datetime."""
    from datetime import UTC

    return datetime.now(UTC)


def list_to_array(data: list[list[float | int]]) -> np.ndarray:
    """Convert a list of lists to a numpy array of float32."""
    return np.array([np.array(x) for x in data]).astype("float32")


def to_date(value: Any) -> date | None:
    """Convert a value to a date if possible."""
    if value:
        with suppress(ValueError, TypeError, ParserError, OutOfBoundsDatetime):
            return pd.to_datetime(value).date()


def to_int(value: Any) -> int | None:
    """Convert a value to an integer if possible."""
    if value is not None:
        with suppress(ValueError):
            return int(value)
