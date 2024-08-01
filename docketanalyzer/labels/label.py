from docketanalyzer.tasks.label_prediction_tasks import LabelPredictions
from docketanalyzer import load_docket_index, pipeline, training_routine


class Label:
    name = None
    label_group = None
    inactive = False
    pipeline_name = 'label'
    parent_labels = None
    routine_name = 'classification'
    base_model = 'docketanalyzer/docket-lm-xs'
    run_args = {'max_length': 256}
    training_args = {
        'num_train_epochs': 1,
        'per_device_train_batch_size': 16,
        'per_device_eval_batch_size': 16,
        'gradient_accumulation_steps': 1,
        'learning_rate': 5e-5,
        'weight_decay': 0.1,
        'warmup_ratio': 0.02,
        'evaluation_strategy': 'steps',
        'eval_steps': 0.08,
        'save_steps': 0.08,
        'save_total_limit': 2,
        'fp16': True,
    }
    minimal_keywords_any = None
    minimal_keywords_all = None

    def __init__(self, index=None):
        if index is None:
            index = load_docket_index()
        self.index = index
        self.cache = {}
    
    @classmethod
    def get_slug(cls):
        return cls.name.lower().replace(' ', '-')

    @property
    def slug(self):
        return self.get_slug()
    
    @property
    def model_name(self):
        return f"docketanalyzer/label-{self.slug}"

    @property
    def train_dir(self):
        return self.index.data_dir / 'runs'
    
    def minimal_condition(self, text):
        if self.minimal_keywords_any is not None:
            if not any(x in text.lower() for x in self.minimal_keywords_any):
                return False
        if self.minimal_keywords_all is not None:
            if not all(x in text.lower() for x in self.minimal_keywords_all):
                return False
        return True

    @property
    def model(self):
        if 'model' not in self.cache:
            from transformers import AutoModelForTokenClassification
            model = pipeline('label', model_name=self.model_name, label=self)
            self.cache['model'] = model
        return self.cache['model']
    
    @property
    def prediction_task(self):
        class_name = self.name.title().replace(' ', '') + 'LabelPredictions'
        attributes = {
            "__doc__": f"Make predictions for {self.name}.",
            "name": f'label-predict-{self.slug}',
            "label_name": self.name
        }
        if self.parent_labels is not None:
            depends_on = []
            for parent_label in self.parent_labels:
                parent_slug = parent_label.get_slug()
                depends_on.append(f'label-predict-{parent_slug}')
            attributes['depends_on'] = depends_on
        globals()[class_name] = type(class_name, (LabelPredictions,), attributes)
        return globals()[class_name](dataset=self.index.dataset)

    @property
    def predictions(self):
        return self.index.label_prediction_dataset.filter(label=self.name)
    
    def train(self, train_data, eval_data, overwrite=False):
        routine = training_routine(
            self.routine_name,
            run_name=self.slug,
            data_dir=self.train_dir,
            base_model=self.base_model,
            push_to_hub=self.model_name,
            run_args=self.run_args,
            training_args=self.training_args,
        )
        routine.train(train_data, eval_data, overwrite=overwrite)
