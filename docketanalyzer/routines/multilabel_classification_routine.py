from sklearn.metrics import f1_score
import torch
from transformers import AutoModelForSequenceClassification, Trainer
from .routine import Routine


class MultilabelTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        loss_fct = torch.nn.BCEWithLogitsLoss()
        loss = loss_fct(logits, labels.float())
        return (loss, outputs) if return_outputs else loss


class MultilabelClassificationRoutine(Routine):
    name = 'multilabel-classification'

    @property
    def label_names(self):
        if 'labels' not in self.run_args:
            raise ValueError('run_args must contain a "labels" key')
        return self.run_args['labels']

    def load_model(self):
        model = AutoModelForSequenceClassification.from_pretrained(
            self.base_model, num_labels=len(self.label_names),
        )
        model.config.label2id = {self.label_names[i]: i for i in range(len(self.label_names))}
        model.config.id2label = {i: self.label_names[i] for i in range(len(self.label_names))}
        return model

    def tokenize_hook(self, examples, inputs):
        inputs['labels'] = torch.tensor([
            [int(label in example_labels) for label in self.label_names]
            for example_labels in examples['labels']
        ])
        return inputs

    def get_trainer_class(self):
        return MultilabelTrainer

    @property
    def compute_metrics(self):
        def f(eval_pred):
            logits, labels = eval_pred
            logits = torch.sigmoid(torch.Tensor(logits)).numpy()
            predictions = (logits > 0.5).astype(int)
            scores = f1_score(predictions, labels, average=None)
            scores = {f"label__{self.label_names[i]}": scores[i] for i in range(len(scores))}
            scores['f1_macro'] = f1_score(predictions, labels, average='macro')
            return scores
        return f
