import sys
from docketanalyzer._version import __version__
from docketanalyzer.utils import *


import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="Valid config keys have changed in V2:")


from docketanalyzer.data import choices
sys.modules[f"docketanalyzer.choices"] = choices


modules = {
    'docketanalyzer.core.chat': {'names': ['Chat', 'ChatThread', 'hello'], 'extras': 'chat'},
    'docketanalyzer.core.database': {'names': ['Database', 'CustomModel', 'connect']},
    'docketanalyzer.core.elastic': {'names': ['load_elastic']},
    'docketanalyzer.core.flp': {'names': ['JuriscraperUtility'], 'extras': 'flp'},
    'docketanalyzer.core.object': {'names': ['ObjectIndex', 'ObjectManager', 'ObjectBatch']},
    'docketanalyzer.core.ocr': {'names': ['extract_pages'], 'extras': 'ocr'},
    'docketanalyzer.core.s3': {'names': ['S3']},
    'docketanalyzer.core.websearch': {'names': ['WebSearch']},
    'docketanalyzer.core.task': {'names': ['Task', 'DocketTask', 'load_tasks', 'load_task', 'register_task', 'task_registry']},
    'docketanalyzer.pipelines': {'names': ['Pipeline', 'pipeline'], 'extras': 'pipelines'},
    'docketanalyzer.pipelines.remote_pipeline': {'names': ['remote_pipeline'], 'extras': 'pipelines'},
    'docketanalyzer.routines': {'names': ['training_routine'], 'extras': 'pipelines'},
    'docketanalyzer.data.docket_index': {'names': ['DocketIndex', 'load_docket_index']},
    'docketanalyzer.data.docket_manager': {'names': ['DocketManager']},
    'docketanalyzer.data.docket_batch': {'names': ['DocketBatch']},
    'docketanalyzer.data.idb': {'names': ['IDB']},
}
lazy_load_modules(modules, globals())


from docketanalyzer.config import *
from docketanalyzer.cli import cli


__all__ = list(set(sum([x['names'] for x in modules.values()], [])))


if dev_available():
    from dev import patch
    patch(globals())
