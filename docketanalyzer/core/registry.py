import importlib
import inspect
import pkgutil
from typing import Any, Optional
from types import ModuleType


class Registry:
    """
    Implement a custom 'find' condition and automatically build a registry of relevant objects in the current module.
    """

    def __init__(self) -> None:
        self._registry: dict[str, Any] = {}
        self.module: ModuleType = inspect.getmodule(inspect.stack()[1][0])

    def register(self, name: str, obj: Any) -> None:
        if name in self._registry:
            raise ValueError(f"'{name}' already exists.")
        self._registry[name] = obj

    def get(self, name: str) -> Any:
        if name not in self._registry:
            raise ValueError(f"'{name}' does not exist.")
        return self._registry[name]

    def all(self) -> list[Any]:
        return list(self._registry.values())

    def find_filter(self, obj: Any) -> bool:
        """
        Add your custom object test here.
        """
        raise NotImplementedError("find_filter() must be implemented by a subclass.")

    def find(self, module: Optional[ModuleType] = None, recurse: bool = False) -> None:
        if module is None:
            module = self.module
        if isinstance(module, str):
            module = importlib.import_module(module)
        for _, submodule_name, _ in pkgutil.walk_packages(module.__path__):
            submodule = importlib.import_module(f"{module.__name__}.{submodule_name}")
            for name in dir(submodule):
                obj = getattr(submodule, name)
                if recurse and isinstance(obj, importlib.machinery.ModuleSpec):
                    next_module = importlib.util.module_from_spec(obj)
                    if hasattr(next_module, '__path__'):
                        self.find(module=next_module)
                if self.find_filter(obj) and name not in self._registry:
                    self.register(name, obj)

    def import_registered(self) -> None:
        """
        Import the registered classes into the current module's namespace.
        """
        for cls in self.all():
            setattr(self.module, cls.__name__, cls)
