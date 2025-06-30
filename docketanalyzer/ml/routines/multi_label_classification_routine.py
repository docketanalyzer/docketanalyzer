import torch
from sklearn.metrics import f1_score
from transformers import AutoModelForSequenceClassification, Trainer

from .routine import Routine


class MultiLabelTrainer(Trainer):
    """Trainer with multi-label loss."""

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        """Compute the loss for multi-label classification."""
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        loss_fct = torch.nn.BCEWithLogitsLoss()
        loss = loss_fct(logits, labels.float())
        return (loss, outputs) if return_outputs else loss


class MultiLabelClassificationRoutine(Routine):
    """Multilabel classification routine.

    Expected data format:

    | text | labels |
    |------|--------|
    | "apple" | ["fruit", "red"] |
    | "banana" | ["fruit", "yellow"] |
    | "orange" | ["fruit", "orange"] |
    | "dog" | ["animal", "mammal"] |
    | "cat" | ["animal", "mammal"] |
    | "bird" | ["animal", "bird"] |
    """

    name = "multi-label-classification"

    @property
    def label_names(self):
        """Get the label names, required in run_args."""
        if "labels" not in self.run_args:
            raise ValueError('run_args must contain a "labels" key')
        return self.run_args["labels"]

    def load_model(self):
        """Load the model."""
        model = AutoModelForSequenceClassification.from_pretrained(
            self.base_model,
            num_labels=len(self.label_names),
            **self.model_args,
        )
        model.config.label2id = {
            self.label_names[i]: i for i in range(len(self.label_names))
        }
        model.config.id2label = {
            i: self.label_names[i] for i in range(len(self.label_names))
        }
        return model

    def tokenize_hook(self, examples, inputs):
        """Tokenize the examples with multi-hot encoded labels."""
        inputs["labels"] = torch.tensor(
            [
                [int(label in example_labels) for label in self.label_names]
                for example_labels in examples["labels"]
            ]
        )
        return inputs

    def get_trainer_class(self):
        """Get the trainer with multi-label loss."""
        return MultiLabelTrainer

    @property
    def compute_metrics(self):
        """Compute f1 scores for each label and macro f1 score."""

        def f(eval_pred):
            logits, labels = eval_pred
            logits = torch.sigmoid(torch.Tensor(logits)).numpy()
            predictions = (logits > 0.5).astype(int)
            scores = f1_score(predictions, labels, average=None)
            scores = {
                f"label__{self.label_names[i]}": scores[i] for i in range(len(scores))
            }
            scores["f1_macro"] = f1_score(predictions, labels, average="macro")
            return scores

        return f


class MultilabelClassificationRoutine(MultiLabelClassificationRoutine):
    """Alias for multi-label classification routine."""

    name = "multilabel-classification"
