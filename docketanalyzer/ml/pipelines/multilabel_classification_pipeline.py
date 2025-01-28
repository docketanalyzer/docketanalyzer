import torch
from transformers import AutoModelForSequenceClassification
from .classification_pipeline import ClassificationPipeline


class MultilabelClassificationPipeline(ClassificationPipeline):
    name = 'multilabel-classification'
    model_class = AutoModelForSequenceClassification
    threshold = 0.5

    def process_outputs(self, outputs, **kwargs):
        return outputs.logits.sigmoid()

    def post_process_preds(self, examples, preds, dataset=None, return_scores=False, **kwargs):
        if return_scores:
            return [
                {
                    'label': [label_name for j, label_name in self.id2label.items() if p[j].item() > self.threshold],
                    'scores': {label_name: p[j].item() for j, label_name in self.id2label.items()}
                } for p in preds
            ]
        return [
            [label_name for j, label_name in self.id2label.items() if p[j].item() > self.threshold]
            for p in preds
        ]
            

    def __call__(self, examples, batch_size=1, return_scores=False):
        return self.predict(examples, batch_size=batch_size, return_scores=return_scores)
