import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"
from contextlib import nullcontext
from copy import deepcopy
from typing import ClassVar

import torch
from datasets import Dataset
from tqdm import tqdm
from transformers import AutoTokenizer


class DataCollator:
    """Data collator."""

    def __init__(self, tokenizer, padding=True, pad_to_multiple_of=8):
        """Initialize the data collator."""
        self.tokenizer = tokenizer
        self.padding = padding
        self.pad_to_multiple_of = pad_to_multiple_of

    def __call__(self, features):
        """Call the data collator."""
        starts, ends = [], []
        for row in features:
            if "offset_mapping" in row:
                offset_mapping = row.pop("offset_mapping")
                starts.append(offset_mapping[:, 0])
                ends.append(offset_mapping[:, 1])
        features = self.tokenizer.pad(
            features, padding=self.padding, pad_to_multiple_of=self.pad_to_multiple_of
        )
        if starts:
            features["starts"] = torch.full(
                features["input_ids"].shape, fill_value=-1, dtype=torch.long
            )
            features["ends"] = torch.full(
                features["input_ids"].shape, fill_value=-1, dtype=torch.long
            )
            for i, (start, end) in enumerate(zip(starts, ends, strict=True)):
                features["starts"][i, : len(start)] = start
                features["ends"][i, : len(end)] = end
        return features


class Pipeline:
    """Base pipeline class."""

    name = None
    model_class = None
    default_model_name = None
    default_tokenizer_name = None
    default_model_args: ClassVar[dict] = dict()
    default_tokenize_args: ClassVar[dict] = dict(
        padding=False, truncation=True, max_length=1024
    )
    dataset_cols: ClassVar[list[str]] = ["input_ids", "attention_mask", "idx"]

    def __init__(
        self,
        model_name=None,
        tokenizer_name=None,
        model_args=None,
        tokenize_args=None,
        num_workers=0,
        device=None,
        bf16=True,
    ):
        """Initialize the pipeline."""
        self.model_name = model_name or self.default_model_name
        self.tokenizer_name = (
            tokenizer_name or self.default_tokenizer_name or self.model_name
        )
        self.model_args = model_args or deepcopy(self.default_model_args)
        self.tokenize_args = tokenize_args or deepcopy(self.default_tokenize_args)
        self.num_workers = num_workers
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.bf16 = bf16
        self.cache = {}
        self.post_init()

    def post_init(self):
        """Hook to extend the __init__ method."""
        pass

    @property
    def model(self):
        """Lazy load the model."""
        if "model" not in self.cache:
            self.cache["model"] = self.load_model()
        return self.cache["model"]

    @property
    def tokenizer(self):
        """Lazy load the tokenizer."""
        if "tokenizer" not in self.cache:
            self.cache["tokenizer"] = self.load_tokenizer()
        return self.cache["tokenizer"]

    @property
    def model_loaded(self):
        """Check if the model is loaded."""
        return "model" in self.cache

    @property
    def id2label(self):
        """Get the mapping for label id to label names."""
        if "id2label" not in self.cache:
            self.cache["id2label"] = self.model.config.id2label
        return self.cache["id2label"]

    @property
    def id2label_type(self):
        """Get the mapping for label id to label types."""
        if "id2label_type" not in self.cache:
            label_types = {k: v.split("-")[0] for k, v in self.id2label.items()}
            label_types = sorted(label_types.items(), key=lambda x: x[0])
            label_types = [x[1] for x in label_types]
            label_type_map = {
                "B": 0,
                "I": 1,
                "O": 2,
            }
            label_types = [label_type_map[label_type] for label_type in label_types]
            self.cache["id2label_type"] = torch.tensor(label_types)
        return self.cache["id2label_type"]

    @property
    def id2entity_name(self):
        """Get the mapping for label id to entity names."""
        if "id2entity_name" not in self.cache:
            self.cache["id2entity_name"] = {
                k: v.split("-")[-1] for k, v in self.id2label.items()
            }
        return self.cache["id2entity_name"]

    @property
    def entity_names(self):
        """Get the entity id to entity names."""
        if "entity_names" not in self.cache:
            entity_names = list(set(self.id2entity_name.values()))
            if "O" in entity_names:
                entity_names.remove("O")
            self.cache["entity_names"] = entity_names
        return self.cache["entity_names"]

    @property
    def id2entity_id(self):
        """Get the mapping for label id to entity ids."""
        if "id2entity_id" not in self.cache:
            entity_names = self.entity_names
            id2entity_id = sorted(self.id2entity_name.items(), key=lambda x: x[0])
            id2entity_id = [
                entity_names.index(x[1]) if x[1] != "O" else -1 for x in id2entity_id
            ]
            self.cache["id2entity_id"] = torch.tensor(id2entity_id)
        return self.cache["id2entity_id"]

    def clear_gpu(self):
        """Delete the model from the GPU cache."""
        if self.model_loaded:
            del self.cache["model"]
            torch.cuda.empty_cache()

    def load_model(self):
        """Load the model."""
        return self.model_class.from_pretrained(self.model_name, **self.model_args)

    def load_tokenizer(self):
        """Load the tokenizer."""
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
        return tokenizer

    def tokenize(self, examples):
        """Tokenize function."""
        return self.tokenizer(examples["text"], **self.tokenize_args)

    def create_dataset(self, examples):
        """Create a dataset from the examples."""
        dataset = Dataset.from_dict(
            dict(text=examples, idx=list(range(len(examples)))), split="train"
        )
        dataset = dataset.map(self.tokenize, batched=True)

        dataset = dataset.map(
            lambda x: {"length": [len(y) for y in x["input_ids"]]}, batched=True
        )
        dataset = dataset.sort("length", reverse=True)
        dataset.set_format(type="torch", columns=self.dataset_cols)
        return dataset

    def create_dataloader(self, dataset, batch_size=1):
        """Create a dataloader from the dataset."""
        dataloader = torch.utils.data.DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=False,
            pin_memory=True,
            num_workers=self.num_workers,
            collate_fn=DataCollator(self.tokenizer),
        )
        return dataloader

    def post_process_preds(self, examples, preds, **kwargs):
        """Post-process predictions hook."""
        return preds

    def process_batch(self, outputs, **kwargs):
        """Process the outputs of a batch."""
        raise NotImplementedError

    def predict(self, examples, batch_size=1, **kwargs):
        """Predict the labels for the examples."""
        num_pad_examples = len(examples) % batch_size
        num_pad_examples = (batch_size - num_pad_examples) % batch_size

        dataset = self.create_dataset(examples)

        preds = [None] * len(dataset)

        dataloader = self.create_dataloader(
            dataset,
            batch_size=batch_size,
        )

        model = self.model
        model.eval().to(self.device)

        with torch.no_grad():
            autocast_context = (
                torch.autocast(self.device, dtype=torch.bfloat16)
                if self.bf16 and self.device == "cuda"
                else nullcontext()
            )
            with autocast_context:
                for batch in tqdm(dataloader, desc="Predicting"):
                    idxs = batch.pop("idx").tolist()
                    inputs = {
                        k: batch[k].to(self.device, non_blocking=False)
                        for k in ["input_ids", "attention_mask"]
                    }
                    outputs = model(**inputs)
                    batch_preds = self.process_batch(batch, outputs, **kwargs)
                    for i, idx in enumerate(idxs):
                        preds[idx] = batch_preds[i]
                    del outputs

        torch.cuda.empty_cache()
        preds = self.post_process_preds(examples, preds, dataset=dataset, **kwargs)
        return preds

    def __call__(self, *args, **kwargs):
        """Add workflow to the predict method."""
        return self.predict(*args, **kwargs)
