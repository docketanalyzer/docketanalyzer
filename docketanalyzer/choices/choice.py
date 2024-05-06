from enum import Enum
from typing import Optional


class Choice(Enum):
    """Base class for all choices."""
    def __new__(
        cls,
        value: str,
        data: Optional[dict] = {},
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data = data
        return obj

    @property
    def data(self):
        return self._data
