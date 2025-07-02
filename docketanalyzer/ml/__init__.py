from docketanalyzer import extension_required

with extension_required("ml"):
    from .pipelines import pipeline
    from .routines import training_routine


__all__ = ["pipeline", "training_routine"]
