import shutil

import pandas as pd

from docketanalyzer import env
from docketanalyzer.ml import pipeline, training_routine


def test_classification():
    """Test classification routine on dummy data."""
    model_dir = env.DATA_DIR / "runs" / "tests" / "classification" / "model"
    if model_dir.exists():
        shutil.rmtree(model_dir)

    data = []
    for label in ["apple", "banana", "orange"]:
        data += [{"text": label, "label": 1} for _ in range(300)]
    for label in ["dog", "cat", "bird"]:
        data += [{"text": label, "label": 0} for _ in range(300)]

    data = pd.DataFrame(data).sample(frac=1)

    split = int(0.8 * len(data))
    train_data = data.head(split)
    eval_data = data.tail(-split)

    routine = training_routine(
        "classification",
        run_name="tests/classification",
        base_model="docketanalyzer/modernbert-unit-test",
        training_args=dict(
            num_train_epochs=1,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            gradient_accumulation_steps=1,
        ),
    )

    routine.train(train_data, eval_data, overwrite=True)

    assert model_dir.exists(), f"Model directory {model_dir} does not exist"

    pipe = pipeline("classification", model_name=str(model_dir))
    preds = pipe(["apple", "banana", "dog", "cat"])

    assert preds == [True, True, False, False]


def test_multilabel_classification():
    """Test multi-label classification routine on dummy data."""
    model_dir = env.DATA_DIR / "runs" / "tests" / "multi-label-classification" / "model"
    if model_dir.exists():
        shutil.rmtree(model_dir)

    text_labels = {
        "apple": ["fruit", "red"],
        "banana": ["fruit", "yellow"],
        "orange": ["fruit", "orange"],
        "dog": ["animal", "mammal"],
        "cat": ["animal", "mammal"],
        "bird": ["animal", "bird"],
    }

    data, label_names = [], []

    for text, labels in text_labels.items():
        data += [{"text": text, "labels": labels} for _ in range(500)]
        label_names += labels

    data = pd.DataFrame(data).sample(frac=1)
    label_names = sorted(list(set(label_names)))

    split = int(0.8 * len(data))
    train_data = data.head(split)
    eval_data = data.tail(-split)

    routine = training_routine(
        "multi-label-classification",
        base_model="docketanalyzer/modernbert-unit-test",
        run_name="tests/multi-label-classification",
        run_args=dict(labels=label_names),
        training_args=dict(
            num_train_epochs=1,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            gradient_accumulation_steps=1,
        ),
    )

    routine.train(train_data, eval_data, overwrite=True)

    assert model_dir.exists(), f"Model directory {model_dir} does not exist"

    pipe = pipeline("multi-label-classification", model_name=str(model_dir))
    print(pipe(["apple", "banana", "dog", "cat"]))

    assert pipe(["apple", "banana", "dog", "bird"]) == [
        ["fruit", "red"],
        ["fruit", "yellow"],
        ["animal", "mammal"],
        ["animal", "bird"],
    ]
