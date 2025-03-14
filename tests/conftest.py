from pathlib import Path

import pytest


@pytest.fixture
def fixture_dir():
    """Path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"
