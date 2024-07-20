from docketanalyzer.labels.label import Label
from docketanalyzer import Registry


class LabelRegistry(Registry):
    def find_filter(self, obj):
        return (
            isinstance(obj, type) and
            issubclass(obj, Label) and
            obj is not Label and
            obj.name is not None and 
            obj.inactive is False
        )


label_registry = LabelRegistry()
label_registry.find()

label_registry.import_registered()


def load_labels():
    return {x.name: x for x in label_registry.all()}


def load_label(name):
    for label in label_registry.all():
        if label.name == name:
            return label


def register_label(label_class):
    label_registry.register(label_class.__name__, label_class)
