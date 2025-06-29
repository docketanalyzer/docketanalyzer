import shutil

import pandas as pd

from docketanalyzer import env
from docketanalyzer.ml import pipeline, training_routine


def test_classification_routine():
    """Test classification routine on dummy data."""
    data = []
    for label in ["apple", "banana", "orange"]:
        data += [{"text": label, "label": 1} for _ in range(100)]
    for label in ["dog", "cat", "bird"]:
        data += [{"text": label, "label": 0} for _ in range(100)]

    data = pd.DataFrame(data).sample(frac=1)

    split = int(0.8 * len(data))
    train_data = data.head(split)
    eval_data = data.tail(-split)

    model_dir = env.DATA_DIR / "runs" / "tests" / "classification" / "model"
    if model_dir.exists():
        shutil.rmtree(model_dir)

    routine = training_routine(
        "classification",
        run_name="tests/classification",
        base_model="docketanalyzer/modernbert-unit-test",
        training_args=dict(
            num_train_epochs=3,
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
