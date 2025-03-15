try:
    import docketanalyzer_pacer  # noqa: F401
except ImportError as e:
    raise ImportError(
        "\n\nPACER extension not installed. "
        "Use `pip install docketanalyzer[pacer]` to install."
    ) from e
from docketanalyzer_pacer import Pacer

__all__ = [
    "Pacer",
]
