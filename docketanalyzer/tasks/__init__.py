from docketanalyzer import Registry
from .task import Task, DocketTask


class TaskRegistry(Registry):
    def find_filter(self, obj):
        return (
            isinstance(obj, type) and
            issubclass(obj, Task) and
            obj is not Task and
            obj.name is not None and 
            obj.inactive is False
        )


task_registry = TaskRegistry()
task_registry.find()


def load_tasks():
    return {x.name: x for x in task_registry.all()}


def load_task(name):
    for task in task_registry.all():
        if task.name == name:
            return task


def register_task(task_class):
    task_registry.register(task_class.__name__, task_class)
