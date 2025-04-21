import simplejson as json
from .. import Registry
from .choice import Choice


class ChoiceRegistry(Registry):
    """Registry for all Choices."""

    def find_filter(self, obj):
        """Filter for finding all Choices."""
        return isinstance(obj, type) and issubclass(obj, Choice) and obj is not Choice

    def dict(self):
        """Return a dictionary of all registered choices."""
        return {obj.__name__: obj.dict() for obj in self}

    def __repr__(self):
        """Return a string representation of the registry."""
        return json.dumps(self.dict(), indent=2)


choices = ChoiceRegistry()
choices.find()
