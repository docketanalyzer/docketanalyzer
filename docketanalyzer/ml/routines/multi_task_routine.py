import torch
from transformers import (
    AutoModelForTokenClassification,
    DataCollatorWithPadding,
    Trainer,
)

from .token_classification_routine import TokenClassificationRoutine


class MultiTaskTrainer(Trainer):
    """Multi-task trainer."""

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        """Compute the loss for multi-task classification."""
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits.reshape((-1, 3))
        labels = labels.reshape((-1, 3))
        mask = labels.sum(-1) != 0
        labels = labels[mask].argmax(-1)
        logits = logits[mask]
        loss_fct = torch.nn.CrossEntropyLoss()
        loss = loss_fct(logits, labels)
        return (loss, outputs) if return_outputs else loss


class MultiTaskDataCollator:
    """Multi-task data collator."""

    def __init__(self, tokenizer, pad_to_multiple_of=8):
        """Initialize the standard data collator."""
        self.collator = DataCollatorWithPadding(
            tokenizer,
            pad_to_multiple_of=pad_to_multiple_of,
        )

    def __call__(self, features):
        """Call the data collator and pad the label vectors."""
        labels = [x.pop("labels") for x in features]
        num_labels = len(labels[0][0])
        batch = self.collator(features)

        padded_labels = torch.zeros(
            (len(labels), batch["input_ids"].shape[1], num_labels)
        )
        for idx in range(len(labels)):
            padded_labels[idx, 0 : len(labels[idx])] = labels[idx]

        batch["labels"] = padded_labels
        return batch


class MultiTaskRoutine(TokenClassificationRoutine):
    """Multi-task routine.

    Notes:
    - All labels get their own BIO outputs.
    - B-labels on the CLS token are treated as sequence-level labels.
    - Labels on the other tokens are treated as span labels.
    """

    name = "multi-task"

    def __init__(self, *args, **kwargs):
        """Initialize the routine, forcing return_offsets_mapping."""
        super().__init__(*args, **kwargs)
        self.run_args["return_offsets_mapping"] = True

    def get_trainer_class(self):
        """Get the trainer class with multi-task loss."""
        return MultiTaskTrainer

    @property
    def label_map(self):
        """Get BIO-encoded label map."""
        if "label_map" not in self.cache:
            label_map = {}
            for label_name in self.label_names:
                label_map["O-" + label_name] = len(label_map)
                label_map["B-" + label_name] = len(label_map)
                label_map["I-" + label_name] = len(label_map)
            self.cache["label_map"] = label_map
        return self.cache["label_map"]

    def load_model(self):
        """Load the model."""
        model = AutoModelForTokenClassification.from_pretrained(
            self.base_model,
            num_labels=len(self.label_map),
            **self.model_args,
        )
        model.config.label2id = self.label_map
        model.config.id2label = {v: k for k, v in self.label_map.items()}
        return model

    @property
    def data_collator(self):
        """Get the data collator."""
        return MultiTaskDataCollator(self.tokenizer, pad_to_multiple_of=8)

    def tokenize_hook(self, examples, inputs):
        """Tokenize the examples and convert labels to multi-task format."""
        labels = []
        for input_ids, offset_mapping, example_spans, example_labels in zip(
            inputs["input_ids"],
            inputs["offset_mapping"],
            examples["spans"],
            examples["labels"],
            strict=False,
        ):
            example_outputs = torch.zeros((len(input_ids), len(self.label_map))).float()

            for label_name in self.label_names:
                if label_name in example_labels:
                    example_outputs[0][self.label_map["B-" + label_name]] = 1
                else:
                    example_outputs[0][self.label_map["O-" + label_name]] = 1

                label_spans = [x for x in example_spans if x["label"] == label_name]
                label_idxs = self.example_spans_to_labels(
                    input_ids,
                    offset_mapping,
                    label_spans,
                    o_idx=self.label_map["O-" + label_name],
                )
                for i, label_idx in enumerate(label_idxs):
                    if label_idx != -100:
                        example_outputs[i][label_idx] = 1
            labels.append(example_outputs)

        inputs["labels"] = labels
        del inputs["offset_mapping"]
        return inputs


"""
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
            scores = {
                f"clf__{self.clf_labels[i]}": scores[i] for i in range(len(scores))
            }
            scores["clf_f1_macro"] = f1_score(clf_preds, clf_labels, average="macro")

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
                scores["ner_" + group + "_f1"] = f1_score(
                    group_preds, group_labels, average="macro"
                )
            return scores

        return f
"""
