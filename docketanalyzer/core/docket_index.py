from datetime import datetime
import pandas as pd
from pathlib import Path
import simplejson as json
from toolz import partition_all
from tqdm import tqdm
from docketanalyzer import load_dataset, JuriscraperUtility, DocketManager
from docketanalyzer.utils import DATA_DIR


class DocketIndex:
    def __init__(self, data_dir=DATA_DIR, local=False):
        self.data_dir = Path(data_dir)
        self.dataset = load_dataset('dockets', pk='docket_id', local=local)
        self.entry_dataset = load_dataset('entries', pk='entry_id', local=local)
        self.doc_dataset = load_dataset('docs', pk='doc_id', local=local)
        self.idb_dataset = load_dataset('idb', pk='idb_row', local=local)
        self.label_dataset = load_dataset('labels', pk='label_id', local=local)
        self.juri = JuriscraperUtility()
        self.cache = {}

    @property
    def tasks(self):
        from docketanalyzer import load_tasks
        return {k: v(dataset=self.dataset) for k, v in load_tasks().items()}

    def add_from_html(self, html, court, append_if_exists=False, add_to_dataset=True):
        docket_parsed = self.juri.parse(html, court)
        docket_id = f"{docket_parsed['court_id']}__{docket_parsed['docket_number'].replace(':', '_')}"
        manager = self[docket_id]
        if not manager.dir.exists():
            manager.dir.mkdir(parents=True)
        if append_if_exists or not manager.docket_html_paths:
            manager.add_docket_html(html)
            if add_to_dataset:
                self.dataset.add(pd.DataFrame({'docket_id': [docket_id]}))
        return manager

    def check_docket_dirs(self):
        """
        Checks if any dockets have been inadverently added to the DATA_DIR without being in the dockets core dataset.
        """
        dockets_dir = self.data_dir / 'dockets'
        dockets_dir.mkdir(parents=True, exist_ok=True)
        docket_ids = pd.DataFrame({'docket_id': [
            x.name for x in dockets_dir.iterdir()
            if x.is_dir() and not x.name.startswith('.')
        ]})

        if len(docket_ids):
            batch_size = 100000
            for batch in tqdm(list(partition_all(batch_size, docket_ids.to_dict('records')))):
                self.dataset.add(pd.DataFrame(batch))
        self.dataset.config['last_checked'] = str(datetime.now())

    def __getitem__(self, docket_id):
        manager = DocketManager(docket_id, data_dir=self.data_dir)
        manager.cache['index'] = self
        return manager

    def __iter__(self):
        for docket_id in tqdm(self.dataset.pandas('docket_id')['docket_id']):
            yield self[docket_id]


def load_docket_index(*args, **kwargs):
    return DocketIndex(*args, **kwargs)
