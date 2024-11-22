import pandas as pd
import torch
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification
from .pipeline import Pipeline


class ClassificationPipeline(Pipeline):
    name = 'classification'
    model_class = AutoModelForSequenceClassification
    tokenize_args = {
        'max_length': 256,
    }
    threshold = 0.5

    @property
    def id2label(self):
        if 'id2label' not in self.cache:
            self.cache['id2label'] = self.model.config.id2label
        return self.cache['id2label']

    def filtered_prediction(self, return_scores=False):
        if return_scores:
            return {'label': False, 'score': 0}
        else:
            return False

    def predict_batch(self, inputs, return_scores=False):
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            return self.model(**inputs).logits.argmax(axis=1).detach().cpu().numpy().astype(bool)

