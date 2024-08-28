from .routine import Routine
from docketanalyzer import Registry


class RoutineRegistry(Registry):
    """
    A registry for all training routines.
    """
    def find_filter(self, obj):
        return isinstance(obj, type) and issubclass(obj, Routine) and obj is not Routine


routine_registry = RoutineRegistry()
routine_registry.find()


def training_routine(name, **kwargs):
    for routine_class in routine_registry.all():
        if routine_class.name == name:
            return routine_class(**kwargs)
    raise ValueError(f'Training Routine "{name}" not found.')
