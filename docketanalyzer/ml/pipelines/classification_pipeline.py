from transformers import AutoModelForSequenceClassification

from .pipeline import Pipeline


class ClassificationPipeline(Pipeline):
    """Pipeline for binary or multi-class classification."""

    name = "classification"
    model_class = AutoModelForSequenceClassification

    @property
    def num_labels(self):
        """Get the number of labels."""
        return len(self.id2label)

    @property
    def is_binary(self):
        """Check if the pipeline is binary."""
        return self.num_labels == 2

    def process_batch(self, batch, outputs, return_scores=False, **kwargs):
        """Apply softmax to the logits."""
        scores = outputs.logits.softmax(dim=-1).cpu()
        if self.is_binary:
            scores = scores[:, 1]
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
                        "label": self.id2label[score.argmax().item()],
                        "scores": {
                            label_name: score[j].item()
                            for j, label_name in self.id2label.items()
                        },
                    }
                    for score in scores
                ]
            return [self.id2label[score.argmax().item()] for score in scores]

    def __call__(self, examples, batch_size=1, return_scores=False):
        """Main entrypoint, expects a list of strings."""
        return self.predict(
            examples, batch_size=batch_size, return_scores=return_scores
        )
