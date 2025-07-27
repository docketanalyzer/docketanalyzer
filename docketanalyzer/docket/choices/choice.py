from enum import Enum


class Choice(Enum):
    """Base class for all choices."""

    def __new__(
        cls,
        value: str,
        data: dict | None = None,
    ):
        """Create a new choice instance.

        A choice can be initialized with just a value, as a standard Enum,
            or as a tuple with a value and additional data dict.
        """
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data = data or {}
        return obj

    @property
    def data(self):
        """Return the data associated with the choice."""
        return self._data

    @classmethod
    def choices(cls):
        """Return a list of tuples containing the choice name and value."""
        return [(x.name, x.value) for x in list(cls)]

    @classmethod
    def dict(cls):
        """Return a dict of the choice name and value."""
        return {x.name: x.value for x in list(cls)}
