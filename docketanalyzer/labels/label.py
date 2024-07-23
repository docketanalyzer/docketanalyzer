from docketanalyzer.tasks.label_prediction_tasks import LabelPredictions
from docketanalyzer import load_docket_index, pipeline


class Label:
    name = None
    label_group = None
    inactive = False
    pipeline_name = 'label'
    parent_labels = None

    def __init__(self, index=None):
        if index is None:
            index = load_docket_index()
        self.index = index
        self.cache = {}
    
    @classmethod
    def get_slug(cls):
        return cls.name.lower().replace(' ', '-')
    
    @property
    def minimal_condition(self):
        return None

    @property
    def slug(self):
        return self.get_slug()
    
    @property
    def model_name(self):
        return f"docketanalyzer/label-{self.slug}"

    @property
    def model(self):
        if 'model' not in self.cache:
            from transformers import AutoModelForTokenClassification
            model = pipeline('label', model_name=self.model_name)
            model.minimal_condition = self.minimal_condition
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
    
    def train(self, train_data, eval_data):
        pass
