from docketanalyzer import load_docket_index, pipeline


class Label:
    name = None
    label_group = None
    inactive = False
    pipeline_name = 'label'

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
    def model(self):
        if 'model' not in self.cache:
            from transformers import AutoModelForTokenClassification
            self.cache['model'] = pipeline('label', model_name=self.model_name)
        return self.cache['model']
    
    @property
    def prediction_task(self):
        task_name = f'label-predict-{self.slug}'
        return self.index.tasks[task_name]
