import tempfile
from pathlib import Path

import pytest

from docketanalyzer.docket import DocketIndex


def test_unknown_attribute_error():
    """Accessing an unknown attribute should raise AttributeError."""
    tmp_dir = Path(tempfile.mkdtemp())
    index = DocketIndex(tmp_dir)
    manager = index["test__1"]
    with pytest.raises(AttributeError):
        _ = manager.hello
