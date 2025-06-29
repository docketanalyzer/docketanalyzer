from docketanalyzer import Registry
from .routine import Routine


class RoutineRegistry(Registry):
    """A registry for all training routines."""

    def find_filter(self, obj):
        """Filter for finding all Routines."""
        return isinstance(obj, type) and issubclass(obj, Routine) and obj is not Routine


routine_registry = RoutineRegistry()
routine_registry.find()
routine_registry.import_registered()


def training_routine(name, **kwargs):
    """Get and initialize a training routine by name."""
    for routine_class in routine_registry.all():
        if routine_class.name == name:
            return routine_class(**kwargs)
    raise ValueError(f'Training Routine "{name}" not found.')
