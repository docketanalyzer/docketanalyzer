from typing import ClassVar

import torch
from transformers import AutoModelForTokenClassification

from .pipeline import Pipeline


class MultiTaskPipeline(Pipeline):
    """Pipeline for multi-task classification."""

    name = "multi-task"
    model_class = AutoModelForTokenClassification
    default_tokenize_args: ClassVar[dict] = dict(
        padding=False, truncation=True, max_length=512, return_offsets_mapping=True
    )
    dataset_cols: ClassVar[list[str]] = [
        "input_ids",
        "attention_mask",
        "offset_mapping",
        "idx",
    ]

    def init_preds(self, dataset, **kwargs):
        """Initialize the prediction tensor."""
        max_len = max(len(x) for x in dataset["input_ids"])

        def get_start_end(inputs):
            start = [x[:, 0].tolist() for x in inputs["offset_mapping"]]
            start = [x + [0] * (max_len - len(x)) for x in start]
            end = [x[:, 1].tolist() for x in inputs["offset_mapping"]]
            end = [x + [0] * (max_len - len(x)) for x in end]
            return dict(start=start, end=end)

        dataset = dataset.map(get_start_end, batched=True)
        dataset = dataset.remove_columns(["offset_mapping"])
        return dataset, torch.zeros(
            (len(dataset), max_len, len(self.model.config.id2label)), dtype=torch.long
        )

    def process_outputs(self, outputs, **kwargs):
        """Argmax the label dimension."""
        original_shape = outputs.logits.shape
        logits = outputs.logits.reshape((-1, 3))
        scores = logits.softmax(-1)
        preds = (scores == scores.max(-1, keepdim=True)[0]).float()
        preds = preds.reshape(original_shape)
        return preds

    def post_process_preds(self, examples, preds, dataset, **kwargs):
        """Convert BIO-encoded labels to labels andspans."""
        id2label = self.model.config.id2label
        dataset = dataset.sort("idx")
        starts = dataset["start"]
        ends = dataset["end"]

        results = []
        for i, example in enumerate(examples):
            labels, spans = [], []

            label_spans = {
                label[2:]: None for label in id2label.values() if label.startswith("B-")
            }

            for tok_idx in range(len(preds[i])):
                if dataset[i]["input_ids"][tok_idx] in [
                    self.model.config.eos_token_id,
                    self.model.config.pad_token_id,
                ]:
                    break

                token_labels = [
                    id2label[label_id]
                    for label_id, value in enumerate(preds[i][tok_idx])
                    if value == 1
                ]
                if tok_idx == 0:  # Add sentence-level labels
                    labels += [
                        label[2:] for label in token_labels if label.startswith("B-")
                    ]
                else:  # Add spans
                    start, end = starts[i][tok_idx], ends[i][tok_idx]

                    for label in token_labels:
                        label_type, label_name = label[:1], label[2:]

                        # Close the span if ended or new
                        if label_spans[label_name] is not None and label_type in [
                            "O",
                            "B",
                        ]:
                            spans.append(label_spans[label_name])
                            label_spans[label_name] = None

                        # Open new spans
                        if label_type == "B":
                            label_spans[label_name] = {
                                "start": start.item(),
                                "end": end.item(),
                                "label": label_name,
                            }

                        # Continue existing spans
                        elif label_type == "I":
                            if label_spans[label_name] is not None:
                                label_spans[label_name]["end"] = end.item()
                            else:  # Open in edge case where it wasn't already
                                label_spans[label_name] = {
                                    "start": start.item(),
                                    "end": end.item(),
                                    "label": label_name,
                                }

            # Close any remaining spans
            for span in label_spans.values():
                if span is not None:
                    spans.append(span)

            # Remove leading spaces
            for span in spans:
                if example[span["start"]] == " ":
                    span["start"] += 1

            spans = list(sorted(spans, key=lambda x: x["start"]))

            results.append(dict(labels=labels, spans=spans))
        return results
