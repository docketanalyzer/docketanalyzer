from docketanalyzer.config import config
import docketanalyzer.utils as utils
from docketanalyzer.core.registry import Registry

from docketanalyzer.utils import LazyLoad

imports = {
    'choices': ['choices'],
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

__all__ = []
for module, names in imports.items():
    for name in names:
        globals()[name] = LazyLoad(f'docketanalyzer.{module}', name)
        __all__.append(name)


class RecapApi:
    pass
