modules = {
    'docketanalyzer_pipelines.parallel_inference': ['parallel_inference'],
    'docketanalyzer_pipelines.pipelines': ['Pipeline', 'pipeline', 'pipeline_registry'],
    'docketanalyzer_pipelines.remote_pipeline': ['remote_pipeline'],
    'docketanalyzer_pipelines.routines': ['Routine', 'training_routine'],
}


from docketanalyzer import lazy_load_modules
lazy_load_modules(modules, globals())
