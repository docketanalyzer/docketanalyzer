from docketanalyzer import choices
from docketanalyzer import load_label, load_labels
from .task import DocketTask


class LabelPredictions(DocketTask):
    name = None
    batch_size = 5000
    workers = None
    depends_on = ['add-entries']
    label_name = None

    def prepare(self):
        self.label = load_label(self.label_name)(index=self.index)
        model = self.label.model
        print(model([
            "Answer to complaint filed by defendant.",
            "Complaint filed by Donald Duck.",
        ]))

    def process(self, batch):
        raise NotImplementedError("task.process or task.process_row must be implemented.")


for label in load_labels().values():
    class_name = label.name.title().replace(' ', '') + 'Predictions'
    globals()[class_name] = type(class_name, (LabelPredictions,), {
        "__doc__": f"Make predictions for {label.name}.",
        "name": f'label-predict-{label.get_slug()}',
        "label_name": label.name
    })
