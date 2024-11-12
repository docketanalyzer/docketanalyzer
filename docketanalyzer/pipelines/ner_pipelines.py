import torch
from transformers import AutoModelForTokenClassification
from .pipeline import Pipeline


class NerPipeline(Pipeline):
    name = 'ner'
    model_class = AutoModelForTokenClassification
    tokenize_args = {
        'max_length': 768,
        'return_offsets_mapping': True,
    }

    @property
    def id2label(self):
        if 'id2label' not in self.cache:
            self.cache['id2label'] = self.model.config.id2label
        return self.cache['id2label']

    def filtered_prediction(self):
        return []
    
    def post_process_predictions(self, texts, preds):
        for i in range(len(preds)):
            for span in preds[i]:
                span['text'] = texts[i][span['start']:span['end']].strip()
        return preds

    def predict_batch(self, inputs):
        offset_mapping = inputs.pop('offset_mapping')
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        preds = []
        with torch.no_grad():
            labels = self.model(**inputs).logits.argmax(-1).detach().cpu().numpy()
            for i in range(labels.shape[0]):
                spans = []
                last_span = None
                for t in range(1, labels.shape[1]):
                    bio_label = self.id2label[labels[i, t]].split('-')
                    label = bio_label[-1]
                    bio = bio_label[0]
                    if bio == 'I':
                        if (last_span is None or label != last_span['label']):
                            bio = 'B'
                        else:
                            last_span['end'] = offset_mapping[i, t][1].item()
                    if last_span is not None and bio in ['B', 'O']:
                        spans.append(last_span)
                        last_span = None
                    if bio == 'B':
                        last_span = {
                            'start': offset_mapping[i, t][0].item(),
                            'end': offset_mapping[i, t][1].item(),
                            'label': label,
                        }
                if last_span is not None:
                    spans.append(last_span)
                preds.append(spans)
        return preds


class EntityPipeline(NerPipeline):
    name = 'ner-entities'
    model_name = 'docketanalyzer/ner-entities'
