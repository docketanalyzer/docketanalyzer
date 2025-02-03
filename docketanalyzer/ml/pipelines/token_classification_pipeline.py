import torch
from transformers import AutoModelForTokenClassification
from .pipeline import Pipeline


class TokenClassificationPipeline(Pipeline):
    name = "token-classification"
    model_class = AutoModelForTokenClassification
    default_tokenize_args = dict(padding=False,truncation=True, max_length=512, return_offsets_mapping=True)
    dataset_cols = ["input_ids", "attention_mask", "offset_mapping", "idx"]

    def init_preds(self, dataset, **kwargs):
        max_len = max(len(x) for x in dataset["input_ids"])
        def get_start_end(inputs):
            start = [x[:, 0].tolist() for x in inputs['offset_mapping']]
            start = [x + [0] * (max_len - len(x)) for x in start]
            end = [x[:, 1].tolist() for x in inputs['offset_mapping']]
            end = [x + [0] * (max_len - len(x)) for x in end]
            return dict(start=start, end=end)
        dataset = dataset.map(get_start_end, batched=True)
        dataset = dataset.remove_columns(['offset_mapping'])
        return dataset, torch.full((len(dataset), max_len), self.model.config.label2id['O'], dtype=torch.long)

    def process_outputs(self, outputs, **kwargs):
        return outputs.logits.argmax(dim=-1)
    
    def post_process_preds(self, examples, preds, dataset, **kwargs):
        id2label = self.model.config.id2label
        dataset = dataset.sort("idx")
        starts = dataset["start"]
        ends = dataset["end"]
        broken = True

        results = []
        for i, _ in enumerate(examples):
            token_ids = preds[i]
            spans = []
            for tok_idx, label_id in enumerate(token_ids):
                label_id = label_id.item()
                if label_id == -1:
                    break
                label = id2label[label_id]
                start, end = starts[i][tok_idx], ends[i][tok_idx]
                if label == 'O':
                    broken = True
                elif label.startswith("B-") or broken:
                    spans.append({"start": start.item(), "end": end.item(), "label": label[2:]})
                    broken = False
                elif label.startswith("I-"):
                    if spans and spans[-1]["label"] == label[2:]:
                        spans[-1]["end"] = end.item()
                    else:
                        spans.append({"start": start.item(), "end": end.item(), "label": label[2:]})
            results.append(spans)
        return results



class NERPipeline(TokenClassificationPipeline):
    name = 'ner'
