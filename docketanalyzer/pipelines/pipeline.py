from datasets import Dataset
from toolz import partition_all
import torch
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer, pipeline
from transformers.pipelines.pt_utils import KeyDataset


class Pipeline:
    name = None
    model_name = None
    tokenizer_name = None
    model_class = AutoModel
    model_defaults = {}
    pipeline_name = None
    pipeline_defaults = {}
    forward_defaults = {}

    def __init__(self, model_name=None, tokenizer_name=None, device=None):
        if model_name is not None:
            self.model_name = model_name
        if tokenizer_name is not None:
            self.tokenizer_name = tokenizer_name
        if self.tokenizer_name is None:
            self.tokenizer_name = self.model_name
        device = device if device is not None else 0 if torch.cuda.is_available() else 'cpu'
        self.cache = {}
        self.model = self.load_model()
        self.model.to(device)
        self.model.eval()
        self.tokenizer = self.load_tokenizer()
        if self.pipeline_name is not None:
            self.pipe = pipeline(
                self.pipeline_name, model=self.model, tokenizer=self.tokenizer,
                device=device, **self.pipeline_defaults,
            )
        
    @property
    def minimal_condition(self):
        return None

    def get_excluded_pred(self, **kwargs):
        return []

    def load_model(self):
        return self.model_class.from_pretrained(self.model_name, **self.model_defaults)

    def load_tokenizer(self):
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
        tokenizer.model_input_names = ['input_ids', 'attention_mask']
        return tokenizer

    def convert_to_dataset(self, texts):
        dataset = Dataset.from_dict({'text': texts})
        return KeyDataset(dataset, 'text')

    def batch_predict(self, texts, **forward_args):
        inputs = self.tokenizer(
            texts, return_tensors='pt', **forward_args
        ).to(self.model.device)
        outputs = self.model(**inputs)
        return outputs.logits.cpu().tolist()

    def model_predict(self, texts, batch_size=1, show_progress=True, **forward_args):
        for k, v in self.forward_defaults.items():
            forward_args[k] = forward_args.get(k, v)
        if self.pipeline_name is None:
            preds = []
            pbar = tqdm(total=len(texts), disable=not show_progress)
            for batch in partition_all(batch_size, texts):
                batch = list(batch)
                preds += self.batch_predict(batch, **forward_args)
                pbar.update(len(batch))
            return preds
        else:
            dataset = self.convert_to_dataset(texts)
            return [
                pred for pred in
                tqdm(
                    self.pipe(dataset, batch_size=batch_size, **forward_args),
                    total=len(texts), disable=not show_progress,
                )
            ]

    def predict(self, texts, **kwargs):
        preds = [self.get_excluded_pred(**kwargs)] * len(texts)
        process_texts = []
        process_texts_map = {}
        for i, text in enumerate(texts):
            if not self.minimal_condition or self.minimal_condition(text):
                process_texts.append(text)
                process_texts_map[len(process_texts) - 1] = i
        model_preds = self.model_predict(process_texts, **kwargs)
        for i, pred in enumerate(model_preds):
            preds[process_texts_map[i]] = pred
        return preds

    def __call__(self, texts, batch_size=1, show_progress=True, **kwargs):
        return self.predict(texts, batch_size=batch_size, show_progress=show_progress, **kwargs)
