import torch
from transformers import AutoModelForTokenClassification
from .pipeline import Pipeline

"""
class MultitaskPipeline(Pipeline):
    name = 'multitask'
    model_class = AutoModelForTokenClassification
    forward_defaults = {
        'padding': 'longest',
        'truncation': True,
        'max_length': 768,
    }

    def __init__(self, max_length=None, **kwargs):
        super().__init__(**kwargs)
        if max_length is not None:
            self.forward_defaults['max_length'] = max_length
        self.cache = {}

    @property
    def clf_labels(self):
        if not 'clf_labels' in self.cache:
            self.cache['clf_labels'] = {
                k: v.split('-')[-1] for k, v in self.model.config.id2label.items()
                if v.startswith('C-')
            }
        return self.cache['clf_labels']

    @property
    def span_groups(self):
        if not 'span_groups' in self.cache:
            span_groups = {}
            for k, v in self.model.config.id2label.items():
                label_type = v.split('-')[0]
                if label_type != 'C':
                    group = v.split('-')[1]
                    if group not in span_groups:
                        span_groups[group] = []
                    span_groups[group].append(k)
                    span_groups[group] = list(sorted(span_groups[group]))
            self.cache['span_groups'] = span_groups
        return self.cache['span_groups']

    def batch_predict(self, texts, output_scores=False, output_groups=False, flat=False, **forward_args):
        inputs = self.tokenizer(
            texts, return_tensors='pt',
            return_offsets_mapping=True,
            **forward_args,
        ).to(self.model.device)
        offset_mapping = inputs.pop('offset_mapping').cpu()
        outputs = self.model(**inputs)
        outputs = outputs.logits.cpu()
        inputs = inputs.to('cpu')

        span_group_preds = {}
        for group, indices in self.span_groups.items():
            group_scores = outputs[:, :, indices]
            group_preds = group_scores.argmax(dim=-1)
            group_preds += min(indices)
            span_group_preds[group] = group_preds
        
        label_scores = outputs[:, 0, :len(self.clf_labels)]
        label_scores = torch.sigmoid(label_scores)
        label_preds = label_scores > 0.5
            
        preds = []
        for i in range(len(texts)):
            pred = {}
            if output_scores:
                pred['label_scores'] = {self.clf_labels[l]: score.item() for l, score in enumerate(label_scores[i])}
            pred['labels'] = [self.clf_labels[l] for l, x in enumerate(label_preds[i]) if x]
            
            spans = []
            for group in span_group_preds:
                current_span = None
                for t in range(1, outputs.shape[1]):
                    if offset_mapping[i][t][1] == 0:
                        break
                    label_id = span_group_preds[group][i][t].item()
                    label = self.model.config.id2label[label_id]
                    if label.startswith('O') or label.startswith('B'):
                        if current_span is not None:
                            spans.append(current_span)
                            current_span = None
                    if label.startswith('B'):
                        current_span = {
                            'start': offset_mapping[i][t][0].item(),
                            'end': offset_mapping[i][t][1].item(),
                            'label': label.split('-')[-1],
                        }
                        if output_groups:
                            current_span['group'] = group
                    elif label.startswith('I') and current_span is not None:
                        current_span['end'] = offset_mapping[i][t][1].item()
                if current_span is not None:
                    spans.append(current_span)
            
            for span in spans:
                span['text'] = texts[i][span['start']:span['end']].strip()
                if texts[i][span['start']] == ' ':
                    span['start'] += 1
                if texts[i][span['end'] - 1] == ' ':
                    span['end'] -= 1

            if not flat:
                spans = sorted(spans, key=lambda x: x['end'] - x['start'])
                processed = []
                for s in range(len(spans)):
                    keep = True
                    span = spans[s]
                    for longer_span in spans[s+1:]:
                        if span['start'] >= longer_span['start'] and span['end'] <= longer_span['end']:
                            longer_span['spans'] = list(sorted(
                                longer_span.get('spans', []) + [span], 
                                key=lambda x: x['start'],
                            ))
                            keep = False
                            break
                    if keep:
                        processed.append(span)
                spans = sorted(processed, key=lambda x: x['start'])
            pred['spans'] = spans

            preds.append(pred)
        return preds
"""