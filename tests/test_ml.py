import pandas as pd


def test_classification(model_dir):
    """Test classification routine on dummy data."""
    from docketanalyzer.ml import pipeline, training_routine

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
        data_dir=model_dir.parents[1],
        run_name=model_dir.parent.name,
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


def test_multi_label_classification(model_dir):
    """Test multi-label classification routine on dummy data."""
    from docketanalyzer.ml import pipeline, training_routine

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
        data_dir=model_dir.parents[1],
        run_name=model_dir.parent.name,
        run_args=dict(labels=label_names),
        training_args=dict(
            num_train_epochs=1,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
        ),
    )

    routine.train(train_data, eval_data, overwrite=True)

    assert model_dir.exists(), f"Model directory {model_dir} does not exist"

    pipe = pipeline("multi-label-classification", model_name=str(model_dir))

    assert pipe(["apple", "banana", "dog", "bird"]) == [
        ["fruit", "red"],
        ["fruit", "yellow"],
        ["animal", "mammal"],
        ["animal", "bird"],
    ]


def test_token_classification(model_dir):
    """Test token classification routine on dummy data."""
    from docketanalyzer.ml import pipeline, training_routine

    texts = [
        "John Doe is a software engineer.",
        "He gave John Doe a raise.",
        "What about John Doe?",
        "John Doe is happy.",
        "Hello, John Doe",
    ]

    data = []

    for text in texts:
        start = text.index("John Doe")
        for _ in range(300):
            data.append(
                {
                    "text": text,
                    "spans": [{"start": start, "end": start + 8, "label": "name"}],
                }
            )

    data = pd.DataFrame(data).sample(frac=1)

    split = int(0.8 * len(data))
    train_data = data.head(split)
    eval_data = data.tail(-split)

    routine = training_routine(
        "token-classification",
        base_model="docketanalyzer/modernbert-unit-test",
        data_dir=model_dir.parents[1],
        run_name=model_dir.parent.name,
        run_args=dict(labels=["name"]),
        training_args=dict(
            num_train_epochs=1,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
        ),
    )

    routine.train(train_data, eval_data, overwrite=True)

    assert model_dir.exists(), f"Model directory {model_dir} does not exist"

    pipe = pipeline("token-classification", model_name=str(model_dir))
    text = "Hello, John Doe"
    pred = pipe([text])[0][0]

    assert text[pred["start"] : pred["end"]] == "John Doe"


def test_multi_task(model_dir):
    """Test multi-task routine on dummy data."""
    from docketanalyzer.ml import pipeline, training_routine

    repeats = 800

    data = dict(
        text=[
            "John Doe is happy.",
            "I think John Doe is sad. And he is human.",
            "hi",
            "wow",
        ]
        * repeats,
        labels=[["happy"], ["sad"], ["sad", "happy"], []] * repeats,
        spans=[
            [
                {"start": 0, "end": 8, "label": "name"},
                {"start": 0, "end": 18, "label": "sentence"},
            ],
            [
                {"start": 8, "end": 16, "label": "name"},
                {"start": 0, "end": 24, "label": "sentence"},
                {"start": 25, "end": 41, "label": "sentence"},
            ],
            [
                {"start": 0, "end": 2, "label": "sentence"},
            ],
            [],
        ]
        * repeats,
    )

    data = pd.DataFrame(data).sample(frac=1)

    split = int(0.8 * len(data))
    train_data = data.head(split)
    eval_data = data.tail(-split)

    routine = training_routine(
        "multi-task",
        base_model="docketanalyzer/modernbert-unit-test",
        data_dir=model_dir.parents[1],
        run_name=model_dir.parent.name,
        run_args=dict(labels=["happy", "sad", "sentence", "name"]),
        training_args=dict(
            num_train_epochs=1,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            learning_rate=2e-3,
        ),
    )

    routine.train(train_data, eval_data, overwrite=True)

    assert model_dir.exists(), f"Model directory {model_dir} does not exist"

    pipe = pipeline("multi-task", model_name=str(model_dir))
    data = data.drop_duplicates(subset=["text"])
    data = data.groupby("text").apply(lambda x: x.to_dict(orient="records")[0])
    texts = data.index.tolist()
    preds = pipe(texts)

    for i in range(len(preds)):
        assert sorted(preds[i]["labels"]) == sorted(data.iloc[i]["labels"]), (
            f"Labels do not match for text {texts[i]}"
        )

        for pred in preds[i]["spans"]:
            del pred["text"]
            del pred["score"]

        assert sorted(
            preds[i]["spans"], key=lambda x: (x["start"], x["end"])
        ) == sorted(data.iloc[i]["spans"], key=lambda x: (x["start"], x["end"])), (
            f"Spans do not match for text {texts[i]}"
        )
