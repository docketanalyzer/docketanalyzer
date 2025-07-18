from docketanalyzer import Registry
from .pipeline import Pipeline


class PipelineRegistry(Registry):
    """A registry for all pipelines."""

    def find_filter(self, obj):
        """Filter the pipelines."""
        return (
            isinstance(obj, type) and issubclass(obj, Pipeline) and obj.name is not None
        )


pipeline_registry = PipelineRegistry()
pipeline_registry.find()
pipeline_registry.import_registered()


def pipeline(name, remote=False, **kwargs):
    """Load and initialize a pipeline by name."""
    if remote:
        raise NotImplementedError("Remote pipelines are not supported yet.")
        from .remote_pipeline import RemotePipeline

        return RemotePipeline(name, **kwargs)
    for pipeline_class in pipeline_registry.all():
        if pipeline_class.name == name:
            return pipeline_class(**kwargs)
    raise ValueError(f'Pipeline "{name}" not found.')
