from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
import math
import multiprocessing
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


def process_inference_batch(texts, pipeline_name, pipeline_args, batch_size=8):
    pipe = pipeline(pipeline_name, **pipeline_args)
    return pipe(texts, batch_size=batch_size)


def parallel_inference(texts, pipeline_name, pipeline_args, workers=2, batch_size=8):
    worker_batch_size = math.ceil(len(texts) / workers)
    worker_batches = [texts[i:i+worker_batch_size] for i in range(0, len(texts), worker_batch_size)]
    try:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(process_inference_batch, batch, pipeline_name, pipeline_args, batch_size) for batch in worker_batches]
            results = [future.result() for future in futures]
        return [item for sublist in results for item in sublist]
    except BrokenProcessPool as e:
        raise BrokenProcessPool("Broken process. Likely you need to wrap your scripts code in an \"if __name__=='__main__'\" block.")
