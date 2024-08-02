from docketanalyzer.tasks.task import Task, DocketTask
from docketanalyzer import Registry, load_labels


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


for task in task_registry.all():
    task.custom = False


def load_tasks():
    return {x.name: x for x in task_registry.all()}


def load_task(name):
    for task in task_registry.all():
        if task.name == name:
            return task


def register_task(task_class):
    task_registry.register(task_class.__name__, task_class)


for label in load_labels().values():
    register_task(label.prediction_task_class)
