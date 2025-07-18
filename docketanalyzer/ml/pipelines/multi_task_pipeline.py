from typing import ClassVar

import torch
from transformers import AutoModelForTokenClassification

from .pipeline import Pipeline


class MultiTaskPipeline(Pipeline):
    """Pipeline for multi-task classification."""

    name = "multi-task"
    model_class = AutoModelForTokenClassification
    default_tokenize_args: ClassVar[dict] = dict(
        padding=False, truncation=True, max_length=1024, return_offsets_mapping=True
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
        """Convert BIO-encoded labels to labels and spans."""
        dataset = dataset.sort("idx")
        batch_size, seq_len, num_labels = preds.shape
        num_groups = num_labels // 3
        tok_idxs = (
            torch.arange(seq_len).repeat_interleave(num_groups).repeat(batch_size)
        )
        max_toks = torch.tensor(
            [len(x) - 1 for x in dataset["input_ids"]]
        ).repeat_interleave(seq_len * num_groups)
        mask = tok_idxs < max_toks
        tok_idxs = tok_idxs[mask]

        example_idxs = torch.arange(batch_size).repeat_interleave(seq_len * num_groups)[
            mask
        ]
        group_idxs = torch.arange(num_groups).repeat(batch_size * seq_len)[mask]
        preds = preds.reshape(-1, 3).argmax(-1)[mask]

        starts = torch.stack(list(dataset["start"]))
        starts = starts.reshape(-1).repeat_interleave(num_groups)[mask]
        ends = torch.stack(list(dataset["end"]))
        ends = ends.reshape(-1).repeat_interleave(num_groups)[mask]

        label_lookup = [
            self.model.config.id2label[i].split("-") for i in range(num_labels)
        ]
        rows = torch.stack(
            [example_idxs, tok_idxs, group_idxs, preds, starts, ends], dim=1
        ).tolist()

        results = []

        current_example = None
        span_groups = {}

        for row in rows:
            example_idx, tok_idx, group_idx, pred, start, end = row
            label_type, label_name = label_lookup[group_idx * 3 + pred]

            if example_idx != current_example:
                if current_example is not None:
                    # Close any remaining spans
                    results[-1]["spans"].extend(span_groups.values())
                    # Remove leading spaces
                    for span in results[-1]["spans"]:
                        if examples[current_example][span["start"]] == " ":
                            span["start"] += 1
                results.append(dict(labels=[], spans=[]))
                current_example = example_idx
                span_groups = {}
            if tok_idx == 0:  # add sentence-level labels
                if label_type == "B":
                    results[-1]["labels"].append(label_name)
            else:  # add spans
                # Close the span if ended or new
                if label_name in span_groups and label_type in [
                    "O",
                    "B",
                ]:
                    results[-1]["spans"].append(span_groups.pop(label_name))

                # Open new spans
                if label_type == "B":
                    span_groups[label_name] = {
                        "start": start,
                        "end": end,
                        "label": label_name,
                    }

                # Continue existing spans
                elif label_type == "I":
                    if label_name in span_groups:
                        span_groups[label_name]["end"] = end
                    else:  # Open in edge case where it wasn't already
                        span_groups[label_name] = {
                            "start": start,
                            "end": end,
                            "label": label_name,
                        }
        return results
