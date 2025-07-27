import importlib
import inspect
import pkgutil
from collections.abc import Generator
from types import ModuleType
from typing import Any


class Registry:
    """Registry base class.

    A registry system that automatically discovers and registers objects based on
        custom criteria.

    Usage example:

    ```python
    from docketanalyzer import Registry
    from somewhere import SomeBaseClass


    class SomeRegistry(Registry):
        def find_filter(self, obj):
            return (
                isinstance(obj, type) and
                issubclass(obj, SomeBaseClass) and
                obj is not SomeBaseClass
            )


    some_registry = SomeRegistry()

    # Find subclasses of SomeBaseClass in this module
    some_registry.find(recurse=True)

    # Import these into the current namespace
    some_registry.import_registered()
    ```
    """

    def __init__(self):
        """Initialize the Registry instance."""
        self._registry: dict[str, Any] = {}
        self.module: ModuleType = inspect.getmodule(inspect.stack()[1][0])

    def register(self, name: str, obj: Any):
        """Register an object with a given name in the registry.

        This method adds an object to the registry with the specified name.

        Args:
            name (str): The name to associate with the object.
            obj (Any): The object to register.

        Raises:
            ValueError: If the name already exists in the registry.
        """
        if name in self._registry:
            raise ValueError(f"'{name}' already exists.")
        self._registry[name] = obj

    def all(self) -> list[Any]:
        """Return a list of all registered objects.

        Returns:
            list: A list of all registered objects in the registry.
        """
        return list(self._registry.values())

    def find_filter(self, obj: Any) -> bool:
        """Determine if an object should be registered based on custom criteria.

        Override this method to define what objects should be registered.
        Should return True for objects that should be included in the registry.

        Args:
            obj (Any): The object to check for registration criteria.

        Returns:
            bool: True if the object matches the criteria, False otherwise.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError(
            "Subclasses must implement find_filter() to define registration criteria."
        )

    def find(self, module: ModuleType | None = None, recurse: bool = False) -> None:
        """Find and register all objects in the module that match find_filter."""
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
                    if hasattr(next_module, "__path__"):
                        self.find(module=next_module)
                if self.find_filter(obj) and name not in self._registry:
                    self.register(name, obj)

    def import_registered(self) -> None:
        """Import the registered classes into the current module's namespace."""
        for cls in self.all():
            setattr(self.module, cls.__name__, cls)

    def dict(self) -> dict[str, Any]:
        """Return a dictionary of all registered objects.

        Returns:
            dict: A dictionary with names as keys and registered objects as values.
        """
        return self._registry

    def __getattr__(self, name: str) -> Any:
        """Retrieve an object from the registry by its name.

        Args:
            name (str): The name of the object to retrieve.

        Returns:
            Any: The object associated with the given name.
        """
        return self._registry[name]

    def __getitem__(self, name: str) -> Any:
        """Retrieve an object from the registry by its name.

        Args:
            name (str): The name of the object to retrieve.

        Returns:
            Any: The object associated with the given name.
        """
        return self._registry[name]

    def __contains__(self, name: str) -> bool:
        """Check if a name exists in the registry.

        Args:
            name (str): The name to check for existence in the registry.

        Returns:
            bool: True if the name exists in the registry, False otherwise.
        """
        return name in self._registry

    def __iter__(self) -> Generator[Any, None, None]:
        """Iterate over all registered objects.

        Yields:
            Any: Each registered object in the registry.
        """
        yield from self._registry.values()

    def __len__(self) -> int:
        """Return the number of registered objects.

        Returns:
            int: The count of registered objects in the registry.
        """
        return len(self._registry)

    def __repr__(self) -> str:
        """Return a string representation of the Registry instance.

        Returns:
            str: A string representation of the registry's registered objects.
        """
        return f"{self.__class__.__name__}({list(self._registry.keys())})"
