from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
import math
import torch
from .pipelines import pipeline


def process_inference_batch(texts, pipeline_name, pipeline_args, batch_size=8):
    pipe = pipeline(pipeline_name, **pipeline_args)
    return pipe(texts, batch_size=batch_size)


def parallel_inference(texts, pipeline_name, pipeline_args, workers=2, batch_size=8):
    auto_device = 'device' not in pipeline_args
    if auto_device:
        auto_device = list(range(torch.cuda.device_count())) * workers
    group_size = math.ceil(len(texts) / workers)
    groups = [texts[i:i+group_size] for i in range(0, len(texts), group_size)]
    try:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = []
            for i, group in enumerate(groups):
                if auto_device:
                    pipeline_args['device'] = auto_device[i]
                    print(pipeline_args)
                futures.append(executor.submit(
                    process_inference_batch, group,
                    pipeline_name, pipeline_args.copy(), batch_size,
                ))
            results = [future.result() for future in futures]
        return [item for sublist in results for item in sublist]
    except BrokenProcessPool as e:
        raise BrokenProcessPool("Broken process. Likely you need to wrap your scripts code in an \"if __name__=='__main__'\" block.")
