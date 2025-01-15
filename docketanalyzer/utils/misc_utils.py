from datetime import datetime, date as datetime_date
from dateutil.parser._parser import ParserError
from functools import wraps
import hashlib
import inspect
import multiprocessing
import secrets
import signal
import string
import subprocess
import time
import numpy as np
import pandas as pd
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from pathlib import Path
import requests
import simplejson as json
from tqdm import tqdm


BASE_DIR = Path(__file__).parents[2]


def fixture_path(path):
    return BASE_DIR / 'tests' / 'fixtures' / path


def demo_data_path(path=None):
    data_dir = BASE_DIR / 'docketanalyzer' / 'data'
    if path is None:
        return list(data_dir.glob('*'))
    return data_dir / path


def bash(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True)
    return out.stdout.strip()


def generate_hash(data, secret=None, length=None):
    data = json.dumps(data, sort_keys=True, default=json_default)
    if secret:
        data += secret
    hash = hashlib.sha256(data.encode()).hexdigest()
    if length:
        hash = hash[:length]
    return hash


def generate_code(length=16):
    abc = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(abc) for _ in range(length))


class timeout:
    """Timeout context manager. Raises TimeoutError if block takes longer than specified time.

    | Example:
    | with timeout(1):
    |     time.sleep(2)
    """
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)


class timeit:
    """Timeit context manager. Measures execution time of block.

    | Example:
    | with timeit('Task'):
    |     time.sleep(1)
    """
    def __init__(self, tag='Task'):
        self.tag = tag
        self.start = None

    def __enter__(self):
        self.start = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = datetime.now()
        execution_time = (end - self.start).total_seconds()
        print(f"{self.tag} took {execution_time:.4f} seconds")


def download_file(url, path, description='Downloading'):
    """Download file from URL to local path with progress bar."""
    path = str(path)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))

    with open(path, 'wb') as file, tqdm(
        desc=description,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress.update(size)


def cpu_workers(p=1):
    if p <= 0 or p > 1:
        raise ValueError("p must be between 0 and 1")
    return int(multiprocessing.cpu_count() * p)


def pd_save_or_append(data, path, **kwargs):
    path = Path(path)
    if path.exists():
        data.to_csv(path, mode='a', header=False, index=False, **kwargs)
    else:
        data.to_csv(path, index=False, **kwargs)


def datetime_utcnow():
    from datetime import UTC
    return datetime.now(UTC)


def list_to_array(value):
    return np.array([np.array(x) for x in value]).astype('float32')


def to_date(value):
    if value:
        try:
            return pd.to_datetime(value).date()
        except (ParserError, OutOfBoundsDatetime):
            pass


def to_int(value):
    if value is not None:
        try:
            return int(value)
        except ValueError:
            pass


def json_default(obj):
    if isinstance(obj, (datetime, datetime_date)):
        return obj.isoformat()


def dev_available():
    return (BASE_DIR / 'dev' / 'docketanalyzer').exists()
