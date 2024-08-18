from docketanalyzer._version import __version__
from docketanalyzer.config import EnvConfig, ConfigKey
import docketanalyzer.utils as utils
from docketanalyzer.core.registry import Registry
import docketanalyzer.choices as choices

from docketanalyzer.utils import lazy_load

imports = {
    'core.chat': ['Chat', 'ChatThread'],
    'core.colab': ['setup_colab'],
    'core.elastic': ['load_elastic'],
    'core.s3': ['S3Utility'],
    'core.juri': ['JuriscraperUtility'],
    'core.ocr': ['extract_pages'],
    'core.websearch': ['WebSearch'],
    'core.core_dataset': ['CoreDataset', 'load_dataset'],
    'core.docket_manager': ['DocketManager'],
    'core.docket_index': ['Index', 'DocketIndex', 'DocketBatch', 'load_docket_index'],
    'core.embeddings': ['Embeddings', 'EmbeddingSample', 'create_embeddings', 'load_embeddings'],
    'pipelines': ['Pipeline', 'pipeline', 'parallel_inference'],
    'routines': ['Routine', 'training_routine'],
    'labels': ['Label', 'LabelRegistry', 'load_labels', 'load_label', 'register_label'],
    'tasks': ['Task', 'DocketTask', 'TaskRegistry', 'load_tasks', 'load_task', 'register_task'],
}


__all__ = ['EnvConfig', 'ConfigKey', 'utils', 'Registry', 'choices']
for module, names in imports.items():
    for name in names:
        globals()[name] = lazy_load(f'docketanalyzer.{module}', name)
        __all__.append(name)


from docketanalyzer.utils import BUILD_MODE
if not BUILD_MODE:
    try:
        import docketanalyzer.dev as dev
        from docketanalyzer.cli import cli
        from docketanalyzer.dev import command_registry
        for command in command_registry.all():
            cli.add_command(command)
        __all__.append('dev')
    except ImportError as e:
        raise e
        pass


class RecapApi:
    pass
