from transformers import AutoModelForTokenClassification
from .pipeline import Pipeline


class NerPipeline(Pipeline):
    name = 'ner'
    model_class = AutoModelForTokenClassification
    pipeline_name = 'token-classification'
    pipeline_defaults = {
        'aggregation_strategy': 'simple',
    }
    forward_defaults = {}
    max_length = 768

    def __init__(self, max_length=None, **kwargs):
        super().__init__(**kwargs)
        self.pipe.tokenizer.model_max_length = max_length or self.max_length

    def __call__(self, texts, batch_size=1, show_progress=True, output_scores=False, **kwargs):
        preds = []
        for i, pred in enumerate(self.predict(texts, batch_size=batch_size, show_progress=show_progress, **kwargs)):
            ps = []
            for p in pred:
                span = {
                    'label': p['entity_group'],
                    'start': p['start'],
                    'end': p['end'],
                    'text': p['word'].strip(),
                }
                if texts[i][span['start']] == ' ':
                    span['start'] += 1
                if texts[i][span['end'] - 1] == ' ':
                    span['end'] -= 1
                if output_scores:
                    span['score'] = p['score']
                ps.append(span)
            preds.append(ps)
        return preds
