from datasets import Dataset
import torch
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer, pipeline


class Pipeline:
    name = None
    model_name = None
    tokenizer_name = None
    model_class = AutoModel
    model_args = {}
    tokenize_args = {}

    def __init__(self, model_name=None, tokenizer_name=None, device=None):
        self.model_name = self.model_name if model_name is None else model_name
        self.tokenizer_name = self.tokenizer_name if tokenizer_name is None else tokenizer_name
        self.tokenizer_name = self.tokenizer_name if self.tokenizer_name is not None else self.model_name
        self.device = device if device is not None else 0 if torch.cuda.is_available() else 'cpu'
        self.cache = {}

        tokenize_args = dict(padding=True, truncation=True, return_tensors='pt')
        tokenize_args.update(self.tokenize_args)
        self.tokenize_args = tokenize_args
        self.post_init()

    def post_init(self):
        pass

    @property
    def model(self):
        if 'model' not in self.cache:
            model = self.load_model()
            model.to(self.device).eval()
            self.cache['model'] = model
        return self.cache['model']
    
    @property
    def tokenizer(self):
        if 'tokenizer' not in self.cache:
            self.cache['tokenizer'] = self.load_tokenizer()
        return self.cache['tokenizer']
        
    def load_model(self):
        return self.model_class.from_pretrained(self.model_name, **self.model_args)

    def load_tokenizer(self):
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
        return tokenizer
    
    def filtered_prediction(self):
        return None
    
    def minimal_condition(self, text):
        return True

    def tokenize_batch(self, batch):
        return self.tokenizer(batch, **self.tokenize_args)
    
    def predict_batch(self, batch):
        raise NotImplementedError

    def pre_process_texts(self, texts):
        return texts

    def post_process_predictions(self, texts, preds):
        return preds

    def __call__(self, texts, batch_size=1, smart_batch=True, verbose=True, **kwargs):
        texts = self.pre_process_texts(texts)
        text_indices = list(range(len(texts)))
        filtered_text_indices = [i for i in text_indices if self.minimal_condition(texts[i])]
        sorted_indices = sorted(filtered_text_indices, key=lambda i: -len(texts[i]))
        sorted_texts = [texts[i] for i in sorted_indices]
        if not smart_batch:
            batches = [sorted_texts[i:i+batch_size] for i in range(0, len(sorted_texts), batch_size)]
            tokenized_batches = [self.tokenize_batch(batch) for batch in batches]
        else:
            progress = tqdm(total=len(sorted_texts), disable=not verbose, desc='Tokenizing')
            max_length = self.tokenize_args.get('max_length', self.model.config.max_position_embeddings)
            max_batch_tokens = batch_size * max_length
            current_position = 0
            tokenized_batches = []
            while current_position < len(sorted_texts):
                batch = sorted_texts[current_position:current_position+batch_size]
                current_position += batch_size
                tokenized_batch = self.tokenize_batch(batch)
                tokenized_batches.append(tokenized_batch)
                max_length = tokenized_batch['input_ids'].shape[-1]
                extra_space = (max_batch_tokens - max_length * batch_size) // max_length
                progress.update(batch_size)
                if extra_space > 0:
                    batch_size += extra_space
        preds = []
        for tokenized_batch in tqdm(tokenized_batches, disable=not verbose, desc='Predicting'):
            preds.extend(self.predict_batch(tokenized_batch, **kwargs))
        resorted_preds = [self.filtered_prediction(**kwargs)] * len(texts)
        for i, j in enumerate(sorted_indices):
            resorted_preds[j] = preds[i]
        resorted_preds = self.post_process_predictions(texts, resorted_preds, **kwargs)
        return resorted_preds


    def new_call(self, texts, batch_size=1, smart_batch=True, verbose=True, max_length=None, **kwargs):
        from docketanalyzer import timeit
        texts = self.pre_process_texts(texts)
        
        max_length = max_length or self.tokenize_args.get('max_length', self.model.config.max_position_embeddings)
        dataset = Dataset.from_dict({'text': texts}, streaming=True)

        def tokenize_function(inputs):
            return self.tokenizer(
                inputs['text'], max_length=max_length, 
                truncation=True, padding=True,
                return_tensors='pt'
            )

        dataset = dataset.map(tokenize_function, batched=True, batch_size=batch_size)
        dataset = dataset.remove_columns(['text'])
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size)
        print(dataloader)


        text_indices = list(range(len(texts)))
        filtered_text_indices = [i for i in text_indices if self.minimal_condition(texts[i])]
        sorted_indices = sorted(filtered_text_indices, key=lambda i: -len(texts[i]))
        sorted_texts = [texts[i] for i in sorted_indices]
        if not smart_batch:
            batches = [sorted_texts[i:i+batch_size] for i in range(0, len(sorted_texts), batch_size)]
            tokenized_batches = [self.tokenize_batch(batch) for batch in batches]
        else:
            progress = tqdm(total=len(sorted_texts), disable=not verbose, desc='Tokenizing')
            max_length = self.tokenize_args.get('max_length', self.model.config.max_position_embeddings)
            max_batch_tokens = batch_size * max_length
            current_position = 0
            tokenized_batches = []
            while current_position < len(sorted_texts):
                batch = sorted_texts[current_position:current_position+batch_size]
                current_position += batch_size
                tokenized_batch = self.tokenize_batch(batch)
                tokenized_batches.append(tokenized_batch)
                max_length = tokenized_batch['input_ids'].shape[-1]
                extra_space = (max_batch_tokens - max_length * batch_size) // max_length
                progress.update(batch_size)
                if extra_space > 0:
                    batch_size += extra_space
        preds = []
        for tokenized_batch in tqdm(tokenized_batches, disable=not verbose, desc='Predicting'):
            preds.extend(self.predict_batch(tokenized_batch, **kwargs))
        resorted_preds = [self.filtered_prediction(**kwargs)] * len(texts)
        for i, j in enumerate(sorted_indices):
            resorted_preds[j] = preds[i]
        resorted_preds = self.post_process_predictions(texts, resorted_preds, **kwargs)
        return resorted_preds
