try:
    import docketanalyzer_chat  # noqa: F401
except ImportError as e:
    raise ImportError(
        "\n\nChat extension not installed. "
        "Use `pip install docketanalyzer[chat]` to install."
    ) from e
from docketanalyzer_chat import Agent, Chat, Field, Tool

__all__ = [
    "Agent",
    "Chat",
    "Field",
    "Tool",
]
