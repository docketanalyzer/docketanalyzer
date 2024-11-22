import torch
from transformers import AutoModel
from .pipeline import Pipeline


class EmbeddingPipeline(Pipeline):
    name = 'embed'
    model_class = AutoModel
    tokenize_args = {
        'max_length': 256,
    }

    def predict_batch(self, inputs):
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
            return outputs.last_hidden_state[:, 0].detach().cpu().numpy()
