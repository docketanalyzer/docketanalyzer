from docketanalyzer._version import __version__
from docketanalyzer.config import config
import docketanalyzer.utils as utils
from docketanalyzer.core.registry import Registry
import docketanalyzer.choices as choices

from docketanalyzer.utils import LazyLoad

imports = {
    'core.chat': ['Chat', 'ChatThread'],
    'core.elastic': ['load_elastic'],
    'core.s3': ['S3Utility'],
    'core.juri': ['JuriscraperUtility'],
    'core.ocr': ['OCRUtility'],
    'core.core_dataset': ['CoreDataset', 'load_dataset'],
    'core.docket_manager': ['DocketManager'],
    'core.docket_index': ['DocketIndex', 'load_docket_index'],
    'core.embeddings': ['Embeddings', 'EmbeddingSample', 'create_embeddings', 'load_embeddings'],
    'pipelines': ['Pipeline', 'pipeline'],
    'routines': ['Routine', 'training_routine'],
    'tasks': ['Task', 'DocketTask', 'load_tasks', 'load_task', 'register_task'],
    'labels': ['Label', 'load_labels', 'load_label', 'register_label'],
    'cli': ['cli'],
}


__all__ = ['config', 'utils', 'Registry', 'choices']
for module, names in imports.items():
    for name in names:
        globals()[name] = LazyLoad(f'docketanalyzer.{module}', name)
        __all__.append(name)


from docketanalyzer.utils import BUILD_MODE
if not BUILD_MODE:
    try:
        import docketanalyzer.dev as dev
        print(BUILD_MODE)
        print(dev)
        from docketanalyzer.cli import cli
        from docketanalyzer.dev import command_registry
        for command in command_registry.all():
            cli.add_command(command)
        __all__.append('dev')
    except ImportError:
        pass


class RecapApi:
    pass
