import pandas as pd
from pathlib import Path
from docketanalyzer import load_dataset, JuriscraperUtility, DocketManager
from docketanalyzer.utils import DATA_DIR


class DocketIndex:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = Path(data_dir)
        self.dataset = load_dataset('dockets')
        self.dataset.set_config('index_col', 'docket_id')
        self.cache = {}

    @property
    def juri(self):
        if 'juri' not in self.cache:
            self.cache['juri'] = JuriscraperUtility()
        return self.cache['juri']

    def add_from_html(self, html, court, append_if_exists=False, add_to_dataset=True):
        docket_parsed = self.juri.parse(html, court)
        if 'court_id' not in docket_parsed:
            print(docket_parsed)
        docket_id = f"{docket_parsed['court_id']}__{docket_parsed['docket_number'].replace(':', '_')}"
        manager = DocketManager(docket_id, data_dir=self.data_dir)
        if not manager.dir.exists():
            manager.dir.mkdir(parents=True)
        if append_if_exists or not manager.docket_html_paths:
            manager.add_docket_html(html)
            if add_to_dataset:
                self.add_to_dataset([docket_id])
        return manager

    def add_to_dataset(self, docket_ids, verbose=False):
        self.dataset.add(pd.DataFrame({'docket_id': docket_ids}), verbose=verbose)
