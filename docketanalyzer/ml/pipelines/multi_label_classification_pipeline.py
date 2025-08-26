from transformers import AutoModelForSequenceClassification

from .classification_pipeline import ClassificationPipeline


class MultiLabelClassificationPipeline(ClassificationPipeline):
    """Pipeline for multi-label classification."""

    name = "multi-label-classification"
    model_class = AutoModelForSequenceClassification
    threshold = 0.5

    def process_batch(self, batch, outputs, return_scores=False, **kwargs):
        """Apply sigmoid to the logits."""
        id2label = self.id2label
        scores = outputs.logits.sigmoid()
        mask = scores > self.threshold
        labels = mask.nonzero(as_tuple=False).cpu().tolist()

        if return_scores:
            scores = scores.cpu().tolist()
            preds = [
                {"labels": [], "scores": {v: scores[i][k] for k, v in id2label.items()}}
                for i in range(mask.shape[0])
            ]
            for idx, label_id in labels:
                preds[idx]["labels"].append(id2label[label_id])
            return preds

        preds = [[] for _ in range(mask.shape[0])]
        for idx, label_id in labels:
            preds[idx].append(id2label[label_id])
        return preds

    def __call__(self, examples, batch_size=1, return_scores=False):
        """Main entrypoint, expects a list of strings."""
        return self.predict(
            examples, batch_size=batch_size, return_scores=return_scores
        )


class MultilabelClassificationPipeline(MultiLabelClassificationPipeline):
    """Alias for multi-label classification pipeline."""

    name = "multilabel-classification"


class MultiLabelPipeline(MultiLabelClassificationPipeline):
    """Alias for multi-label classification pipeline."""

    name = "multi-label"


class MultilabelPipeline(MultiLabelClassificationPipeline):
    """Alias for multi-label classification pipeline."""

    name = "multilabel"
