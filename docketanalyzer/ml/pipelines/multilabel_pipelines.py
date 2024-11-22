import torch
from transformers import AutoModelForSequenceClassification
from .pipeline import Pipeline


class MultilabelPipeline(Pipeline):
    name = 'multilabel'
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
            return [{'label': l, 'score': 0} for l in self.id2label.values()]
        else:
            return []

    def post_process_predictions(self, texts, preds, return_scores=False):
        if not return_scores:
            for i in range(len(preds)):
                preds[i] = [p['label'] for p in preds[i] if p['score'] > self.threshold]
        return preds

    def predict_batch(self, inputs, return_scores=False):
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        preds = []
        with torch.no_grad():
            scores = torch.sigmoid(self.model(**inputs).logits).detach().cpu().numpy()
            for i in range(scores.shape[0]):
                pred = []
                for l in range(1, scores.shape[1]):
                    pred.append({
                        'label': self.id2label[l],
                        'score': scores[i, l],
                    })
                preds.append(pred)
        return preds


class DocketLabelPipeline(MultilabelPipeline):
    name = 'docket-labels'
    model_name = 'docketanalyzer/docket-labels-2'

    def post_init(self):
        if self.model.device.type == 'cuda':
            self.model.half()

    def pre_process_texts(self, texts):
        from docketanalyzer import extract_attachments, extract_entered_date, mask_text_with_spans

        def f(text):
            attachments = extract_attachments(text)
            entered_date = extract_entered_date(text)
            text = mask_text_with_spans(text, attachments + entered_date, mapper=lambda text, span: ' ')
            text = ' '.join(text.split())
            return text

        return [f(text) for text in texts]


class MotionTypePipeline(MultilabelPipeline):
    name = 'motion-types'
    model_name = 'docketanalyzer/motion-types'

    def post_init(self):
        if self.model.device.type == 'cuda':
            self.model.half()

    def minimal_condition(self, text):
        return 'motion' in text.lower()
