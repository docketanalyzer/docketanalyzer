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

    def process_batch(self, batch, outputs, **kwargs):
        """Process the batch."""
        logits = outputs.logits
        original_shape = logits.shape

        id2entity_name = self.id2entity_name
        entity_names = self.entity_names
        starts = batch["starts"]
        ends = batch["ends"]

        scores = logits.view(*original_shape[:2], len(entity_names), 3).softmax(-1)
        labels = scores.argmax(-1)
        scores = scores.gather(-1, labels.unsqueeze(-1)).squeeze(-1)
        valid = (ends.to(logits.device) > 0).unsqueeze(-1)

        sequence_labels = labels[:, 0, :]
        labels = labels.where(valid, torch.full_like(labels, 2))
        scores = scores.where(valid, torch.zeros_like(scores))

        is_B = labels == 0
        is_I = labels == 1
        is_O = labels == 2

        prev_is_O = torch.zeros_like(is_O)
        prev_is_O[:, 1:, :] = is_O[:, :-1, :]
        start_mask = is_B | (is_I & prev_is_O)

        next_is_I = torch.zeros_like(is_I)
        next_is_I[:, :-1, :] = is_I[:, 1:, :]
        end_mask = (~is_O) & (~next_is_I)
        end_mask[:, -1, :] |= ~is_O[:, -1, :]

        start_mask = start_mask.detach().cpu()
        end_mask = end_mask.detach().cpu()
        scores = scores.detach().cpu()

        preds = []
        for i in range(original_shape[0]):
            spans = []

            for label_idx in range(len(entity_names)):
                example_start_idxs = torch.nonzero(
                    start_mask[i, :, label_idx], as_tuple=False
                ).flatten()
                example_end_idxs = torch.nonzero(
                    end_mask[i, :, label_idx], as_tuple=False
                ).flatten()
                for span_idx in range(
                    min(len(example_start_idxs), len(example_end_idxs))
                ):
                    start_idx = example_start_idxs[span_idx].item()
                    end_idx = example_end_idxs[span_idx].item()
                    spans.append(
                        {
                            "start": starts[i, start_idx].item(),
                            "end": ends[i, end_idx].item(),
                            "label": id2entity_name[label_idx * 3],
                            "score": (
                                scores[i, start_idx : end_idx + 1, label_idx]
                                .mean()
                                .item()
                            ),
                        }
                    )

            example_labels = []
            for label_idx in range(len(entity_names)):
                if sequence_labels[i, label_idx] == 0:
                    example_labels.append(id2entity_name[label_idx * 3])

            preds.append({"spans": spans, "labels": example_labels})

        return preds

    def post_process_preds(self, examples, preds, **kwargs):
        """Post-process predictions hook."""
        for i, pred in enumerate(preds):
            for span in pred["spans"]:
                span_text = examples[i][span["start"] : span["end"]]
                if span_text and span_text[0] == " ":
                    span["start"] += 1
                    span_text = span_text[1:]
                span["text"] = span_text
        return preds
