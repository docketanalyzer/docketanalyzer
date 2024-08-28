from docketanalyzer import Registry
from .pipeline import Pipeline


class PipelineRegistry(Registry):
    """
    A registry for all pipelines.
    """
    def find_filter(self, obj):
        return isinstance(obj, type) and issubclass(obj, Pipeline) and obj.name is not None


pipeline_registry = PipelineRegistry()
pipeline_registry.find()


def pipeline(name, **kwargs):
    for pipeline_class in pipeline_registry.all():
        if pipeline_class.name == name:
            return pipeline_class(**kwargs)
    raise ValueError(f'Pipeline "{name}" not found.')
