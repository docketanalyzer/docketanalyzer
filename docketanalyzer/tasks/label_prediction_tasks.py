from docketanalyzer import choices
from .task import DocketTask


class LabelPredictions(DocketTask):
    name = None
    batch_size = 20000
    workers = None
    depends_on = ['add-entries']
    label_name = None

    def post_reset(self, selected_ids):
        filter_args = {'label': self.label_name}
        if selected_ids is not None:
            filter_args['docket_id__in'] = selected_ids
        if selected_ids is None:
            self.index.label_prediction_dataset.filter(**filter_args).delete()

    def prepare(self):
        from docketanalyzer import load_label
        self.label = load_label(self.label_name, index=self.index)
        model = self.label.model

    def process(self, batch):
        docket_ids = batch.pandas('docket_id')['docket_id'].tolist()
        try:
            self.index.label_prediction_dataset.filter(docket_id__in=docket_ids, label=self.label.name).delete()
        except AttributeError:
            pass
        entries = self.index.make_batch([x.docket_id for x in list(batch)]).get_entries()
        if self.label.parent_labels is not None:
            parent_label_names = [x.name for x in self.label.parent_labels]
            keep_entries = self.index.label_prediction_dataset.filter(docket_id__in=docket_ids, label__in=parent_label_names)
            keep_entries = list(keep_entries.pandas('entry_id')['entry_id'].unique())
            entries = entries[entries['entry_id'].isin(keep_entries)]
        entries['label'] = self.label.name
        entries['value'] = self.label.model(entries['description'], batch_size=8)
        entries = entries[entries['value']]
        entries['pred_id'] = entries['entry_id'] + '__' + self.label.slug
        entries = entries[['pred_id', 'entry_id', 'docket_id', 'label']]
        self.index.label_prediction_dataset.add(entries)
