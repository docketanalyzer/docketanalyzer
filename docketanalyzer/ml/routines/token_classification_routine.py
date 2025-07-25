from transformers import (
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
)

from .routine import Routine


class TokenClassificationRoutine(Routine):
    """Token classification routine.

    Expected data format:

    | text | spans |
    |------|-------|
    | "John Doe is a software engineer." | [{"start": 0, "end": 8, "label": "name"}] |
    """

    name = "token-classification"

    def __init__(self, *args, **kwargs):
        """Initialize the routine, forcing return_offsets_mapping."""
        super().__init__(*args, **kwargs)
        self.run_args["return_offsets_mapping"] = True

    @property
    def label_names(self):
        """Get the label names, required in run_args."""
        if "labels" not in self.run_args:
            raise ValueError('run_args must contain a "labels" key')
        return self.run_args["labels"]

    @property
    def label_map(self):
        """Get BIO-encoded label map."""
        if "label_map" not in self.cache:
            label_map = {"O": 0}
            for label_name in sorted(self.label_names):
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
        """Get the token classification data collator."""
        return DataCollatorForTokenClassification(self.tokenizer, pad_to_multiple_of=8)

    def tokenize_hook(self, examples, inputs):
        """Tokenize the examples with BIO-encoded labels."""
        labels = []
        for input_ids, offset_mapping, spans in zip(
            inputs["input_ids"],
            inputs["offset_mapping"],
            examples["spans"],
            strict=False,
        ):
            labels.append(
                self.example_spans_to_labels(input_ids, offset_mapping, spans)
            )
        inputs["labels"] = labels
        del inputs["offset_mapping"]
        return inputs

    def example_spans_to_labels(self, input_ids, offset_mapping, spans, o_idx=0):
        """Convert spans to BIO-encoded labels."""
        spans = sorted(spans, key=lambda x: x["start"])

        labels = []
        current_label = None
        for i in range(len(input_ids)):
            offset = offset_mapping[i]

            if len(spans) > 0 and offset[0] >= spans[0]["end"]:
                spans.pop(0)
                current_label = None

            if offset[1] == 0:
                labels.append(-100)
                current_label = None
            elif len(spans) == 0 or offset[1] <= spans[0]["start"]:
                labels.append(o_idx)
                current_label = None
            else:
                if current_label is None:
                    current_label = spans[0]["label"]
                    labels.append(self.label_map["B-" + current_label])
                else:
                    labels.append(self.label_map["I-" + current_label])
        return labels


class NERRoutine(TokenClassificationRoutine):
    """Alias for token classification routine."""

    name = "ner"
