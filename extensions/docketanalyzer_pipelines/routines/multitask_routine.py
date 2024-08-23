from sklearn.metrics import f1_score
from transformers import AutoModelForTokenClassification, Trainer
import torch
from .routine import Routine


class MultitaskTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits

        loss_fct = torch.nn.BCEWithLogitsLoss()
        num_clf_labels = len(self.routine.clf_labels)
        clf_labels = labels[:, 0, :num_clf_labels]
        clf_logits = logits[:, 0, :num_clf_labels]
        losses = {'clf_loss': loss_fct(clf_logits, clf_labels) * self.routine.weights['clf']}

        loss_fct = torch.nn.CrossEntropyLoss()
        for group in self.routine.span_label_groups:
            label_map = self.routine.group_label_maps[group]
            group_indices = list(label_map.values())
            group_labels = labels[:, :, group_indices]
            group_labels = group_labels.reshape(-1, len(group_indices))
            filter_col = group_labels.sum(-1) == 1
            group_labels = group_labels[filter_col]
            group_logits = logits[:, :, group_indices]
            group_logits = group_logits.reshape(-1, len(group_indices))
            group_logits = group_logits[filter_col]
            group_logits = torch.nn.functional.log_softmax(group_logits, dim=-1)
            losses['span_' + group + '_loss'] = loss_fct(group_logits, group_labels) * self.routine.weights[group]

        loss = sum(losses.values())
        if self.args.logging_steps > 0 and self.state.global_step % self.args.logging_steps == 0:
            self.log({k: v.item() for k, v in losses.items()})
        return (loss, outputs) if return_outputs else loss


class MultitaskRoutine(Routine):
    name = 'multitask'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_args['return_offsets_mapping'] = True

    def get_trainer_class(self):
        return MultitaskTrainer

    @property
    def weights(self):
        if 'weights' not in self.run_args:
            raise ValueError('run_args must contain a "weights" key')
        return self.run_args['weights']

    @property
    def clf_labels(self):
        if 'clf_labels' not in self.run_args:
            raise ValueError('run_args must contain a "clf_labels" key')
        return self.run_args['clf_labels']
    
    @property
    def span_label_groups(self):
        if 'span_label_groups' not in self.run_args:
            raise ValueError('run_args must contain a "span_label_groups" key')
        return self.run_args['span_label_groups']

    @property
    def label_map(self):
        if 'label_map' not in self.cache:
            label_map = {}
            for label in self.clf_labels:
                label_name = label.upper().replace(' ', '_')
                label_map['C-' + label_name] = len(label_map)

            group_label_maps = {}
            for group, labels in self.span_label_groups.items():
                group_name = group.upper().replace(' ', '_')
                group_label_maps[group] = {}
                label_map['O-' + group_name] = len(label_map)
                group_label_maps[group]['O'] = label_map['O-' + group_name]
                for label in labels:
                    label_name = group_name + '-' + label.upper().replace(' ', '_')
                    label_map['B-' + label_name] = len(label_map)
                    label_map['I-' + label_name] = len(label_map)
                    group_label_maps[group]['B-' + label_name] = label_map['B-' + label_name]
                    group_label_maps[group]['I-' + label_name] = label_map['I-' + label_name]
            self.cache['label_map'] = label_map
            self.cache['group_label_maps'] = group_label_maps
        return self.cache['label_map']
    
    @property
    def group_label_maps(self):
        if 'group_label_maps' not in self.cache:
            self.label_map
        return self.cache['group_label_maps']

    def load_model(self):
        model = AutoModelForTokenClassification.from_pretrained(
            self.base_model, num_labels=len(self.label_map),
        )
        model.config.label2id = self.label_map
        model.config.id2label = {v: k for k, v in self.label_map.items()}
        return model

    def tokenize_hook(self, examples, inputs):
        labels = []
        for input_ids, offset_mapping, example_spans, example_clf in zip(inputs['input_ids'], inputs['offset_mapping'], examples['spans'], examples['labels']):
            example_labels = torch.zeros((len(input_ids), len(self.label_map))).float()
            for label in self.clf_labels:
                if label in example_clf:
                    label_name = label.upper().replace(' ', '_')
                    example_labels[0][self.label_map['C-' + label_name]] = 1
            for group in self.span_label_groups:
                span_labels = self.spans_group_to_labels(input_ids, offset_mapping, example_spans, group)
                for i, label in enumerate(span_labels):
                    if label != -100:
                        example_labels[i][label] = 1
            example_labels = example_labels.unsqueeze(0)
            labels.append(example_labels)
        
        inputs['labels'] = torch.cat(labels, dim=0)
        del inputs['offset_mapping']
        return inputs

    def spans_group_to_labels(self, input_ids, offset_mapping, spans, group):
        group_name = group.upper().replace(' ', '_')
        label_map = self.group_label_maps[group]
        spans = [x for x in spans if x['label'] in self.span_label_groups[group]]
        spans = sorted(spans, key=lambda x: x['start'])
        O_id = label_map['O']

        labels = []
        current_label = None
        for i in range(len(input_ids)):
            offset = offset_mapping[i]

            if len(spans) > 0 and offset[0] >= spans[0]['end']:
                spans.pop(0)
                current_label = None

            if offset[1] == 0:
                labels.append(-100)
                current_label = None
            elif len(spans) == 0 or offset[1] <= spans[0]['start']:
                labels.append(O_id)
                current_label = None
            else:
                if current_label is None:
                    current_label = group_name + '-' + spans[0]['label'].upper().replace(' ', '_')
                    labels.append(label_map['B-' + current_label])
                else:
                    labels.append(label_map['I-' + current_label])
        return labels
    
    @property
    def compute_metrics(self):
        def f(eval_pred):
            logits, labels = eval_pred
            num_clf_labels = len(self.clf_labels)
            clf_labels = labels[:, 0, :num_clf_labels]
            clf_logits = logits[:, 0, :num_clf_labels]
            clf_scores = torch.sigmoid(torch.Tensor(clf_logits)).numpy()
            clf_preds = (clf_logits > 0.5).astype(int)
            scores = f1_score(clf_preds, clf_labels, average=None)
            scores = {f"clf__{self.clf_labels[i]}": scores[i] for i in range(len(scores))}
            scores['clf_f1_macro'] = f1_score(clf_preds, clf_labels, average='macro')

            for group in self.span_label_groups:
                label_map = self.group_label_maps[group]
                group_indices = list(label_map.values())
                group_labels = labels[:, :, group_indices]
                group_labels = group_labels.reshape(-1, len(group_indices))
                filter_col = group_labels.sum(-1) != 0
                group_labels = group_labels[filter_col].argmax(-1)
                group_logits = logits[:, :, group_indices]
                group_logits = group_logits.reshape(-1, len(group_indices))
                group_preds = group_logits.argmax(-1)
                group_preds = group_preds[filter_col]
                scores['ner_' + group + '_f1'] = f1_score(group_preds, group_labels, average='macro')
            return scores
        return f
