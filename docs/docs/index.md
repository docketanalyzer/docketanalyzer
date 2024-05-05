# Overview

``` bash
pip install docketanalyzer
```


## Registry

The registry class allows you to automatically collect and import objects in a module that meet some condition.

``` py
from docketanalyzer import Registry

class CustomRegistry(Registry):
    def find_filter(self, obj):
        # create a filter for subclasses of MyCustomBaseClass
        return isinstance(obj, type) and issubclass(obj, BaseJob) and obj is not MyCustomBaseClass


registry = CustomRegistry()

registry.find(recurse=True) # add classes to registry

some_class = registry.get('SomeCustomClass') # access an object by name
all_classes = registry.all() # iterate all objects

registry.import_registered() # import objects into current namespace.
```