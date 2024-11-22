from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests
from tqdm import tqdm
from docketanalyzer import RUNPOD_API_KEY, REMOTE_INFERENCE_ENDPOINT_ID


class RemotePipeline:
    def __init__(self, name, api_key=RUNPOD_API_KEY, endpoint_id=REMOTE_INFERENCE_ENDPOINT_ID, max_retries=3, timeout=60, **args):
        self.name = name
        self.args = args
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.base_url = f'https://api.runpod.ai/v2/{endpoint_id}/'
        self.max_retries = max_retries
    
    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.api_key}'}
    
    def get_inputs(self, texts, **args):
        return {
            'input': {
                'pipeline': {
                    'name': self.name,
                    'args': self.args.copy(),
                },
                'texts': texts,
                **args,
            }
        }
    
    def process_job(self, job):
        error = False
        try:
            job['status'] = job['status'].json()
        except requests.exceptions.JSONDecodeError as e:
            error = True
        if not job['status'].get('status') == 'COMPLETED':
            print(job['status'])
        if not error:
            if 'error' in job['status'] or job['status']['status'] == 'FAILED':
                error = True
        
        if error:
            print('Error:', job['status'])
            job['retries'] = job.get('retries', 0) + 1
            if job['retries'] >= self.max_retries:
                raise Exception(job['status']['error'])
            job = self.create_job(job['i'], job['inputs'])
            self.flurry(8)
        return job
    
    def create_job(self, i, texts, **args):
        inputs = self.get_inputs(texts, **args)
        status = requests.post(
            self.base_url + 'run', 
            headers=self.headers,
            json=inputs,
        )
        job = {'i': i, 'status': status, 'inputs': inputs}
        job = self.process_job(job)
        return job

    def update_job(self, job):
        if job['status']['status'] != 'COMPLETED':
            job['status'] = requests.get(
                self.base_url + 'status/' + job['status']['id'], 
                headers=self.headers,
            )
            job = self.process_job(job)
        return job
    
    def flurry(self, n=8):
        texts = ['A'] * n
        self(texts, group_size=1)
    
    def __call__(self, texts, group_size=None, return_results=True, **args):
        if group_size is None:
            r = requests.post(
                self.base_url + 'runsync', 
                headers=self.headers,
                json=self.get_inputs(texts, **args),
            )
            results = r.json()
            if return_results:
                results = results['output']['results']
            return results
        else:
            jobs = []
            print('Preparing jobs')
            with ThreadPoolExecutor(24) as executor:
                for i, j in enumerate(range(0, len(texts), group_size)):
                    job_texts = texts[j:j+group_size]
                    jobs.append(executor.submit(self.create_job, i, job_texts, **args))
            jobs = [job.result() for job in as_completed(jobs)]

            progress = tqdm(total=len(jobs), desc='Progress')
            while 1:
                with ThreadPoolExecutor(24) as executor:
                    jobs = [executor.submit(self.update_job, job) for job in jobs]
                    jobs = [job.result() for job in as_completed(jobs)]
                num_complete = sum(job['status']['status'] == 'COMPLETED' for job in jobs)
                progress.n = num_complete
                progress.refresh()
                if num_complete == len(jobs):
                    break
                time.sleep(1)
            progress.close()
            
            results = []
            for job in sorted(jobs, key=lambda x: x['i']):
                results.extend(job['status']['output']['results'])
            return results


def remote_pipeline(name, **args):
    return RemotePipeline(name, **args)
