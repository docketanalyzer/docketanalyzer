from docketanalyzer import choices
from docketanalyzer import load_label
from .task import DocketTask


class LabelPredictions(DocketTask):
    """
    Make predictions for labels.
    """
    name = 'label-predict-complaint'
    batch_size = 5000
    workers = None
    depends_on = ['add-entries']
    label_name = 'complaint'

    def prepare(self):
        self.label = load_label(self.label_name)(index=self.index)

    def process(self, batch):
        raise NotImplementedError("task.process or task.process_row must be implemented.")
