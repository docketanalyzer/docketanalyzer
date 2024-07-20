from transformers import AutoModelForSequenceClassification
from .pipeline import Pipeline


class LabelPipeline(Pipeline):
    name = 'label'
    model_name = None
    model_class = AutoModelForSequenceClassification
    pipeline_name = 'text-classification'
    pipeline_defaults = {
        'function_to_apply': 'softmax',
    }
    forward_defaults = {
        'truncation': True,
        'max_length': 256,
    }

    def get_excluded_pred(self, **kwargs):
        return {'label': 'False', 'score': 1.0}

    def __call__(self, texts, batch_size=1, show_progress=True, output_scores=False, **kwargs):
        preds = self.predict(texts, batch_size=batch_size, show_progress=show_progress, **kwargs)
        for pred in preds:
            pred['label'] = pred['label'] == 'True'
        if not output_scores:
            preds = [p['label'] for p in preds]
        return preds
