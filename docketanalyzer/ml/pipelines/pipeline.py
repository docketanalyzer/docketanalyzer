import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
from copy import deepcopy
from contextlib import nullcontext
from datasets import Dataset
import torch
from transformers import AutoTokenizer, DataCollatorWithPadding
from tqdm import tqdm


class Pipeline:
    name = None
    model_class = None
    default_model_name = None
    default_tokenizer_name = None
    default_model_args = dict()
    default_tokenize_args = dict(padding=False, truncation=True, max_length=512)
    dataset_cols = ["input_ids", "attention_mask", "idx"]

    def __init__(self, model_name=None, tokenizer_name=None, model_args=None, tokenize_args=None, num_workers=0, device=None, bf16=True, smart_sort=True):
        self.model_name = model_name or deepcopy(self.default_model_name)
        self.tokenizer_name = tokenizer_name or deepcopy(self.default_tokenizer_name) or self.model_name
        self.model_args = model_args or deepcopy(self.default_model_args)
        self.tokenize_args = tokenize_args or deepcopy(self.default_tokenize_args)
        self.num_workers = num_workers
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.bf16 = bf16
        self.smart_sort = smart_sort
        self.cache = {}
        self.post_init()
    
    def post_init(self):
        pass

    @property
    def model(self):
        if 'model' not in self.cache:
            self.cache['model'] = self.load_model()
        return self.cache['model']
    
    @property
    def tokenizer(self):
        if 'tokenizer' not in self.cache:
            self.cache['tokenizer'] = self.load_tokenizer()
        return self.cache['tokenizer']
    
    @property
    def model_loaded(self):
        return 'model' in self.cache

    def clear_gpu(self):
        if self.model_loaded:
            del self.cache['model']
            torch.cuda.empty_cache()
        
    def load_model(self):
        return self.model_class.from_pretrained(self.model_name, **self.model_args)

    def load_tokenizer(self):
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
        return tokenizer

    def tokenize(self, examples):
        return self.tokenizer(examples['text'], **self.tokenize_args)

    def create_dataset(self, examples):
        dataset = Dataset.from_dict(dict(text=examples, idx=list(range(len(examples)))), split='train')
        dataset = dataset.map(self.tokenize, batched=True)
        if self.smart_sort:
            dataset = dataset.map(lambda x: {'length': [len(y) for y in x['input_ids']]}, batched=True)
            dataset = dataset.sort("length", reverse=True)
        dataset.set_format(type="torch", columns=self.dataset_cols)
        return dataset

    def create_dataloader(self, dataset, batch_size=1):
        dataloader = torch.utils.data.DataLoader(
            dataset, batch_size=batch_size, shuffle=False,
            pin_memory=True, num_workers=self.num_workers,
            collate_fn=DataCollatorWithPadding(self.tokenizer, padding=True, pad_to_multiple_of=8),
        )
        return dataloader

    def pre_process_examples(self, examples, **kwargs):
        return examples

    def post_process_preds(self, examples, preds, **kwargs):
        return preds

    def init_preds(self, dataset, **kwargs):
        raise NotImplementedError

    def process_outputs(self, outputs, **kwargs):
        raise NotImplementedError
    
    def predict(self, examples, batch_size=1, **kwargs):
        examples = self.pre_process_examples(examples, **kwargs)
        dataset = self.create_dataset(examples)
        
        dataset, preds = self.init_preds(dataset, **kwargs)
        idxs = torch.empty(len(dataset), dtype=torch.long)

        dataloader = self.create_dataloader(
            dataset, batch_size=batch_size,
        )

        model = self.model

        model.eval().to(self.device)
        start_idx = 0
        with torch.no_grad():
            autocast_context = (
                torch.autocast(self.device, dtype=torch.bfloat16) if self.bf16 and self.device == 'cuda' else nullcontext()
            )
            with autocast_context:
                for batch in tqdm(dataloader, desc="Predicting"):
                    batch_len = batch["input_ids"].shape[0]
                    idxs[start_idx:start_idx + batch_len] = batch["idx"]
                    del batch["idx"]
                    batch = {k: batch[k].to(self.device, non_blocking=False) for k in ['input_ids', 'attention_mask']}
                    outputs = model(**batch)
                    batch_preds = self.process_outputs(outputs, **kwargs).cpu()
                    preds[start_idx:start_idx + batch_len, :batch_preds.shape[1]] = batch_preds[:, :preds.shape[1]]
                    start_idx += batch_len
                    del outputs
                    torch.cuda.empty_cache()

        idxs = idxs.argsort()
        preds = preds[idxs]
        preds = self.post_process_preds(examples, preds, dataset=dataset, **kwargs)
        return preds

    def __call__(self, *args, **kwargs):
        return self.predict(*args, **kwargs)
