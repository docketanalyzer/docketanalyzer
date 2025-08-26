from typing import ClassVar

import torch
from transformers import AutoModelForTokenClassification

from .pipeline import Pipeline


class TokenClassificationPipeline(Pipeline):
    """Pipeline for token classification."""

    name = "token-classification"
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

        id2label_type = self.id2label_type.to(logits.device)
        id2entity_id = self.id2entity_id.to(logits.device)
        entity_names = self.entity_names
        starts = batch["starts"]
        ends = batch["ends"]

        scores, labels = logits.softmax(-1).max(-1)

        valid = ends.to(logits.device) > 0
        entity_ids = id2entity_id[labels]
        entity_ids = entity_ids * valid + (~valid) * (-1)
        label_types = id2label_type[labels]
        label_types = label_types * valid

        is_B = label_types == 0
        is_I = label_types == 1
        is_O = label_types == 2

        prev_is_O = torch.zeros_like(is_O)
        prev_is_O[:, 1:] = is_O[:, :-1]
        prev_ent_diff = torch.zeros_like(is_O, dtype=torch.bool)
        prev_ent_diff[:, 1:] = entity_ids[:, 1:] != entity_ids[:, :-1]
        start_mask = is_B | (is_I & (prev_is_O | prev_ent_diff))

        next_is_I = torch.zeros_like(is_I)
        next_is_I[:, :-1] = is_I[:, 1:]
        next_ent_diff = torch.zeros_like(is_I, dtype=torch.bool)
        next_ent_diff[:, :-1] = entity_ids[:, :-1] != entity_ids[:, 1:]
        end_mask = (~is_O) & (~next_is_I | next_ent_diff)
        end_mask[:, -1] |= ~is_O[:, -1]

        preds = []
        scores = scores.detach().cpu()
        entity_ids = entity_ids.detach().cpu()
        start_mask = start_mask.detach().cpu()
        end_mask = end_mask.detach().cpu()

        for i in range(len(batch["input_ids"])):
            example_start_idxs = torch.nonzero(start_mask[i], as_tuple=False).flatten()
            example_end_idxs = torch.nonzero(end_mask[i], as_tuple=False).flatten()
            spans = []
            for span_idx in range(min(len(example_start_idxs), len(example_end_idxs))):
                start_idx = example_start_idxs[span_idx].item()
                end_idx = example_end_idxs[span_idx].item()
                entity_id = entity_ids[i, start_idx].item()
                if entity_id < 0:
                    continue
                spans.append(
                    {
                        "start": starts[i, start_idx].item(),
                        "end": ends[i, end_idx].item(),
                        "label": entity_names[entity_id],
                        "score": scores[i, start_idx : end_idx + 1].mean().item(),
                    }
                )
            preds.append(spans)

        return preds

    def post_process_preds(self, examples, preds, **kwargs):
        """Post-process predictions hook."""
        for i, pred in enumerate(preds):
            for span in pred:
                span_text = examples[i][span["start"] : span["end"]]
                if span_text and span_text[0] == " ":
                    span["start"] += 1
                    span_text = span_text[1:]
                span["text"] = span_text
        return preds


class NERPipeline(TokenClassificationPipeline):
    """Alias for token classification pipeline."""

    name = "ner"
