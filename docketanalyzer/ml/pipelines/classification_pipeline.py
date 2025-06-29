import torch
from transformers import AutoModelForSequenceClassification

from .pipeline import Pipeline


class ClassificationPipeline(Pipeline):
    """Pipeline for binary or multi-class classification."""

    name = "classification"
    model_class = AutoModelForSequenceClassification

    @property
    def id2label(self):
        """Get the id2label mapping."""
        if "id2label" not in self.cache:
            self.cache["id2label"] = self.model.config.id2label
        return self.cache["id2label"]

    @property
    def num_labels(self):
        """Get the number of labels."""
        return len(self.id2label)

    @property
    def is_binary(self):
        """Check if the pipeline is binary."""
        return self.num_labels == 2

    def init_preds(self, dataset, **kwargs):
        """Initialize the prediction tensor."""
        return dataset, torch.zeros(len(dataset), self.num_labels)

    def process_outputs(self, outputs, **kwargs):
        """Apply softmax to the logits."""
        return outputs.logits.softmax(dim=-1)

    def post_process_preds(
        self, examples, preds, dataset=None, return_scores=False, **kwargs
    ):
        """Return the labels and scores for binary or multi-class classification."""
        if self.is_binary:
            scores = preds[:, 1]
            labels = (scores > 0.5).tolist()
            if return_scores:
                return [
                    {"label": label, "score": score}
                    for label, score in zip(labels, scores.tolist(), strict=False)
                ]
            return labels
        else:
            if return_scores:
                return [
                    {
                        "label": self.id2label[p.argmax().item()],
                        "scores": {
                            label_name: p[j].item()
                            for j, label_name in self.id2label.items()
                        },
                    }
                    for p in preds
                ]
            return [self.id2label[p.argmax().item()] for p in preds]

    def __call__(self, examples, batch_size=1, return_scores=False):
        """Main entrypoint, expects a list of strings."""
        return self.predict(
            examples, batch_size=batch_size, return_scores=return_scores
        )
