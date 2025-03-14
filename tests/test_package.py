import logging
import subprocess
import sys

from docketanalyzer import notabs


def test_import_time():
    """Test the import time of the package."""
    timing_code = notabs("""
        import time
        start = time.time()
        import docketanalyzer
        end = time.time()
        print(end - start)
    """)

    result = subprocess.run(
        [sys.executable, "-c", timing_code], capture_output=True, text=True, check=True
    )

    import_time = float(result.stdout.strip())

    logging.info(f"docketanalyzer import time: {import_time:.4f} seconds")
    assert import_time < 1, f"Import time is too long: {import_time} seconds"
