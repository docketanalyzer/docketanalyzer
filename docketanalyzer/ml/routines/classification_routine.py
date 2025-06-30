from typing import ClassVar

import torch
from sklearn.metrics import f1_score
from transformers import AutoModelForSequenceClassification

from .routine import Routine


class ClassificationRoutine(Routine):
    """Binary classification routine.

    Expected data format:

    | text | label |
    |------|-------|
    | "apple" | 1 |
    | "banana" | 0 |
    | "orange" | 1 |
    | "dog" | 0 |
    """

    name = "classification"
    dataset_cols: ClassVar[list[str]] = ["input_ids", "attention_mask", "label"]

    @property
    def label_names(self):
        """Get the label names or set default."""
        if "label_names" not in self.cache:
            self.cache["label_names"] = self.run_args.get("labels", ["False", "True"])
        return self.cache["label_names"]

    def load_model(self):
        """Load the model."""
        # Noticed better performance with num_labels=2
        # i.e. using softmax instead of sigmoid
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
        if not model.config.pad_token_id:
            model.config.pad_token_id = model.config.eos_token_id
        return model

    def tokenize_hook(self, examples, inputs):
        """Tokenize the examples with one-hot encoded labels."""
        inputs["labels"] = torch.tensor(
            [
                example_label
                if isinstance(example_label, int)
                else self.label_names.index(example_label)
                for example_label in examples["label"]
            ]
        ).long()
        return inputs

    @property
    def compute_metrics(self):
        """Compute f1 score for evaluation."""

        def f(eval_pred):
            logits, labels = eval_pred
            predictions = logits.argmax(axis=1).astype(int)
            score = f1_score(
                labels,
                predictions,
                average="binary" if len(self.label_names) == 2 else "macro",
            )
            return {"f1": score}

        return f
