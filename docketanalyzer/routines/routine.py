from datetime import datetime
import shutil
from datasets import Dataset
from pathlib import Path
import simplejson as json
from transformers import (
    AutoTokenizer,
    TrainingArguments,
    Trainer,
)
from docketanalyzer import DATA_DIR


class Routine:
    name = None

    def __init__(
        self,
        run_name,
        base_model,
        push_to_hub=None,
        run_args={},
        training_args={},
        data_dir=DATA_DIR / 'runs',
    ):
        self.run_name = run_name
        self.base_model = base_model
        self.push_to_hub = push_to_hub
        self.run_args = run_args
        self.training_args = training_args
        self.data_dir = Path(data_dir)

        self.train_dataset = None
        self.eval_dataset = None
        self.cache = {}

    @property
    def config(self):
        return {
            'base_model': self.base_model,
            'run_args': self.run_args,
            'training_args': self.training_args,
            'run_name': self.run_name,
            'run_type': self.run_type,
        }

    @property
    def run_type(self):
        return self.__class__.__name__

    @property
    def run_dir(self):
        return self.data_dir / self.run_name

    @property
    def config_path(self):
        return self.run_dir / 'run_config.json'

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
        self.run_dir.mkdir(parents=True, exist_ok=True)
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
        return None

    @property
    def tokenize_function(self):
        text_cols = self.run_args.get('text_cols', ['text'])
        max_length = self.run_args.get('max_length', 1024)
        return_offsets_mapping = self.run_args.get('return_offsets_mapping', False)

        def f(examples):
            inputs = self.tokenizer(
                *[examples[x] for x in text_cols],
                padding="max_length",
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
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
            logging_dir=self.run_dir / 'logs',
            logging_strategy='steps',
            logging_steps=2,
            remove_unused_columns=False,
        )
        if self.push_to_hub is not None:
            args['push_to_hub'] = True
            args['hub_model_id'] = self.push_to_hub
            args['hub_strategy'] = 'end'
            args['hub_private_repo'] = True
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
        train_dataset.set_transform(self.tokenize_function)
        if eval_dataset is not None:
            eval_dataset.set_transform(self.tokenize_function)

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

    def train(self, train_data, eval_data=None, overwrite=False):
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
            (self.run_dir / 'eval_results.json').write_text(
                json.dumps(results, indent=4)
            )
            print(results)
        self.tokenizer.save_pretrained(self.run_dir)
        self.trainer.save_model(self.run_dir)
        self.trainer.push_to_hub()
        (self.run_dir / 'complete.txt').write_text(str(datetime.now()))
