from docketanalyzer.choices.choice import Choice
from docketanalyzer import Registry


class ChoiceRegistry(Registry):
    def find_filter(self, obj):
        return isinstance(obj, type) and issubclass(obj, Choice) and obj is not Choice


choice_registry = ChoiceRegistry()
choice_registry.find()

choice_registry.import_registered()
