from transformers import AutoModelForSequenceClassification

from .classification_pipeline import ClassificationPipeline


class MultiLabelClassificationPipeline(ClassificationPipeline):
    """Pipeline for multi-label classification."""

    name = "multi-label-classification"
    model_class = AutoModelForSequenceClassification
    threshold = 0.5

    def process_outputs(self, outputs, **kwargs):
        """Apply sigmoid to the logits."""
        return outputs.logits.sigmoid()

    def post_process_preds(
        self, examples, preds, dataset=None, return_scores=False, **kwargs
    ):
        """Return the labels and scores for multi-label classification."""
        if return_scores:
            return [
                {
                    "labels": [
                        label_name
                        for j, label_name in self.id2label.items()
                        if p[j].item() > self.threshold
                    ],
                    "scores": {
                        label_name: p[j].item()
                        for j, label_name in self.id2label.items()
                    },
                }
                for p in preds
            ]
        return [
            [
                label_name
                for j, label_name in self.id2label.items()
                if p[j].item() > self.threshold
            ]
            for p in preds
        ]

    def __call__(self, examples, batch_size=1, return_scores=False):
        """Main entrypoint, expects a list of strings."""
        return self.predict(
            examples, batch_size=batch_size, return_scores=return_scores
        )


class MultilabelClassificationPipeline(MultiLabelClassificationPipeline):
    """Alias for multi-label classification pipeline."""

    name = "multilabel-classification"
