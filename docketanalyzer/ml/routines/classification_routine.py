from sklearn.metrics import f1_score
import torch
from transformers import AutoModelForSequenceClassification
from .routine import Routine


class ClassificationRoutine(Routine):
    name = 'classification'

    @property
    def label_names(self):
        return ["False", "True"]

    def load_model(self):
        model = AutoModelForSequenceClassification.from_pretrained(
            self.base_model, num_labels=2,
        )
        model.config.label2id = {self.label_names[i]: i for i in range(len(self.label_names))}
        model.config.id2label = {i: self.label_names[i] for i in range(len(self.label_names))}
        if not model.config.pad_token_id:
            model.config.pad_token_id = model.config.eos_token_id
        return model

    def tokenize_hook(self, examples, inputs):
        if 0:
            inputs['labels'] = torch.tensor([
                [0, 1] if example_label else [1, 0]
                for example_label in examples['label']
            ])
        else:
            inputs['labels'] = torch.tensor([
                int(example_label) for example_label in examples['label']
            ])
        return inputs

    @property
    def compute_metrics(self):
        def f(eval_pred):
            logits, labels = eval_pred
            predictions = logits.argmax(axis=1).astype(int)
            labels = labels[:, 1].astype(int)
            score = f1_score(labels, predictions, average='binary')
            return {'f1': score}
        return f
