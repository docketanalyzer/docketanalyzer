from datetime import datetime
from functools import wraps
import inspect
import multiprocessing
import os
import signal
import subprocess
import time
import numpy as np
import pandas as pd
from pathlib import Path
import requests
from tqdm import tqdm


def bash(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True)
    return out.stdout.strip()


class timeout:
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


def cpu_workers(n):
    if n < 1:
        n = multiprocessing.cpu_count() * n
    return int(n)


def pd_save_or_append(data, path, **kwargs):
    path = Path(path)
    if path.exists():
        data.to_csv(path, mode='a', header=False, index=False, **kwargs)
    else:
        data.to_csv(path, index=False, **kwargs)


def rotate_ip():
    """
    Requires PIA VPN to be installed and running.
    """
    current_region = bash(['piactl', 'get', 'region'])
    regions = bash(['piactl', 'get', 'regions']).split('\n')
    regions = [
        x for x in regions
        if x not in ['auto', current_region] and
        not x.startswith('dedicated')
    ]
    np.random.shuffle(regions)
    bash(['piactl', 'set', 'region', regions[0]])
    bash(['piactl', 'connect'])
    while 1:
        time.sleep(1)
        status = bash(['piactl', 'get', 'connectionstate'])
        if status == 'Connected':
            break


def require_confirmation(message="Are you sure you want to proceed?"):
    message += "\n(y/n): "
    confirmation = input(message).lower()
    return confirmation == 'y'


def require_confirmation_wrapper(message="Are you sure you want to proceed?", disable=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())

            all_args = {}
            for i, arg in enumerate(args):
                if i < len(param_names):
                    all_args[param_names[i]] = arg
            all_args.update(kwargs)

            if disable is not None:
                if disable(all_args):
                    return func(*args, **kwargs)

            if callable(message):
                prompt = message(all_args)
            else:
                prompt = message
            
            if require_confirmation(prompt):
                return func(*args, **kwargs)
            else:
                print("Aborted.")
                return None
        return wrapper
    return decorator
