from datetime import datetime
import gc
import shutil
import time
from datasets import Dataset
from huggingface_hub import create_repo, upload_folder
from pathlib import Path
import requests
import simplejson as json
import torch
from transformers import (
    AutoTokenizer,
    DataCollatorWithPadding,
    TrainingArguments,
    Trainer,
)
from docketanalyzer import env, S3


class Routine:
    name = None
    dataset_cols = ['input_ids', 'attention_mask', 'labels']

    def __init__(
        self,
        run_name,
        base_model,
        push_to_hub=None,
        run_args={},
        training_args={},
        model_args={},
        data_dir=None,
    ):
        self.run_name = run_name
        self.base_model = base_model
        self.push_to_hub = push_to_hub
        self.run_args = run_args
        self.training_args = training_args
        self.model_args = model_args
        self.data_dir = Path(data_dir or (env.DATA_DIR / 'runs'))

        self.train_dataset = None
        self.eval_dataset = None
        self.cache = {}

    @property
    def config(self):
        return {
            'run_name': self.run_name,
            'base_model': self.base_model,
            'push_to_hub': self.push_to_hub,
            'run_args': self.run_args,
            'training_args': self.training_args,
            'model_args': self.model_args,
            'routine': self.name,
        }

    @property
    def run_dir(self):
        return self.data_dir / self.run_name
    
    @property
    def model_dir(self):
        return self.run_dir / 'model'

    @property
    def config_path(self):
        return self.model_dir / 'run_config.json'
    
    @property
    def eval_results_path(self):
        return self.model_dir / 'eval_results.json'

    @property
    def model(self):
        if self.cache.get('model') is None:
            self.cache['model'] = self.load_model()
        return self.cache.get('model')

    @property
    def tokenizer(self):
        if self.cache.get('tokenizer') is None:
            self.cache['tokenizer'] = self.load_tokenizer()
        return self.cache.get('tokenizer')

    @property
    def trainer(self):
        if self.cache.get('trainer') is None:
            self.cache['trainer'] = self.load_trainer()
        return self.cache.get('trainer')

    def init(self):
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.config, indent=4))

    def prepare_data(self, train_data, eval_data):
        self.train_dataset = Dataset.from_pandas(train_data)
        self.eval_dataset = None if eval_data is None else Dataset.from_pandas(eval_data)

    def load_model(self):
        raise NotImplementedError

    def load_tokenizer(self):
        tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        if not tokenizer.pad_token:
            tokenizer.pad_token = tokenizer.eos_token
        return tokenizer

    @property
    def data_collator(self):
        return DataCollatorWithPadding(self.tokenizer, pad_to_multiple_of=8)

    @property
    def tokenize_function(self):
        text_cols = self.run_args.get('text_cols', ['text'])
        max_length = self.run_args.get('max_length', 1024)
        return_offsets_mapping = self.run_args.get('return_offsets_mapping', False)

        def f(examples):
            inputs = self.tokenizer(
                *[examples[x] for x in text_cols],
                padding=False,
                truncation=True,
                max_length=max_length,
                return_offsets_mapping=return_offsets_mapping,
            )
            inputs = self.tokenize_hook(examples, inputs)
            return inputs
        return f

    @property
    def compute_metrics(self):
        return None

    @property
    def callbacks(self):
        return None

    def tokenize_hook(self, examples, inputs):
        return inputs

    def get_training_args(self):
        args = dict(
            output_dir=self.run_dir,
            logging_dir=self.model_dir / 'logs',
            logging_strategy='steps',
            logging_steps=2,
            remove_unused_columns=False,
        )
        for k, v in self.training_args.items():
            args[k] = v
        return TrainingArguments(**args)

    def get_trainer_class(self):
        return Trainer

    def trainer_args_hook(self, args):
        return args

    def trainer_hook(self, trainer):
        return trainer

    def load_trainer(self):
        train_dataset, eval_dataset = self.train_dataset, self.eval_dataset
        train_dataset = train_dataset.map(self.tokenize_function, batched=True)
        train_dataset.set_format(type="torch", columns=self.dataset_cols)
        if eval_dataset is not None:
            eval_dataset = eval_dataset.map(self.tokenize_function, batched=True)
            eval_dataset.set_format(type="torch", columns=self.dataset_cols)

        args = {
            'model': self.model,
            'args': self.get_training_args(),
            'train_dataset': train_dataset,
        }

        if eval_dataset is not None:
            args['eval_dataset'] = eval_dataset

        data_collator = self.data_collator
        if data_collator is not None:
            args['data_collator'] = data_collator

        compute_metrics = self.compute_metrics
        if compute_metrics is not None:
            args['compute_metrics'] = compute_metrics

        callbacks = self.callbacks
        if callbacks is not None:
            args['callbacks'] = callbacks

        trainer_class = self.get_trainer_class()
        args = self.trainer_args_hook(args)
        print(args)
        trainer = trainer_class(**args)
        trainer.routine = self
        return self.trainer_hook(trainer)

    def train(self, train_data, eval_data=None, overwrite=False, remote=False):
        if remote:
            return self.train_remote(train_data, eval_data)
        if self.run_dir.exists():
            if overwrite:
                shutil.rmtree(self.run_dir)
            else:
                raise ValueError(f'Run directory already exists: {self.run_dir}')
        self.prepare_data(train_data, eval_data)
        self.init()
        self.trainer.train()
        if eval_data is not None:
            results = self.trainer.evaluate()
            self.eval_results_path.write_text(
                json.dumps(results, indent=4)
            )
            print(results)
        self.tokenizer.save_pretrained(self.model_dir)
        self.trainer.save_model(self.model_dir)
        del self.cache['model']
        del self.cache['trainer']
        gc.collect()
        torch.cuda.empty_cache()
        if self.push_to_hub:
            create_repo(self.push_to_hub, private=True, exist_ok=True)
            upload_folder(
                repo_id=self.push_to_hub,
                folder_path=str(self.model_dir.resolve()),
            )
        (self.run_dir / 'complete.txt').write_text(str(datetime.now()))

    def train_remote(self, train_data, eval_data=None):
        if self.run_dir.exists():
            shutil.rmtree(self.run_dir)

        self.init()
        train_data.to_csv(self.run_dir / 'train.csv', index=False)
        if eval_data is not None:
            eval_data.to_csv(self.run_dir / 'eval.csv', index=False)
        
        s3 = S3()
        s3.push(self.run_dir, delete=True, exact_timestamps=True)

        data_dir = self.data_dir.relative_to(env.DATA_DIR)
        inputs = dict(input=dict(run_name=self.run_name, data_dir=str(data_dir)))
        headers = {'Authorization': f'Bearer {env.RUNPOD_API_KEY}'}
        endpoint_url = f'https://api.runpod.ai/v2/{env.REMOTE_ROUTINES_ENDPOINT_ID}/'
        status = requests.post(
            endpoint_url + 'run', headers=headers, json=inputs,
        ).json()
        job_id = status['id']

        while 1:
            time.sleep(5)
            status = requests.get(endpoint_url + 'status/' + job_id, headers=headers).json()
            print(status)
            if status['status'] == 'COMPLETED':
                break
        