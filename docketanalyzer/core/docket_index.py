from datetime import datetime
import pandas as pd
from pathlib import Path
import simplejson as json
from toolz import partition_all
from tqdm import tqdm
from docketanalyzer import load_dataset, JuriscraperUtility, DocketManager
from docketanalyzer.utils import DATA_DIR


class DocketIndex:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = Path(data_dir)
        self.dataset = load_dataset('dockets', pk='docket_id')
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
        manager = self[docket_id]
        if not manager.dir.exists():
            manager.dir.mkdir(parents=True)
        if append_if_exists or not manager.docket_html_paths:
            manager.add_docket_html(html)
            if add_to_dataset:
                self.add_to_dataset([docket_id])
        return manager

    def add_to_dataset(self, docket_ids, verbose=False):
        self.dataset.add(pd.DataFrame({'docket_id': docket_ids}), verbose=verbose)

    def purchase_docket(self, docket_id, update=False):
        raise NotImplementedError("finish this")
        # think throuugh how the updating from_date will depend on the consolidated json
        manager = self[docket_id]
        if update or not manager.docket_html_paths:
            candidates = self.juri.find_candidates(docket_id)
            if len(candidates) == 1:
                # add update args here
                html = self.juri.purchase_docket_with_pacer_case_id(
                    docket_id.split('__')[0], candidates[0]['pacer_case_id'],
                )
                manager.add_docket_html(html)
            else:
                print(json.dumps(candidates, indent=2))
                raise ValueError(f"Multiple candidates found for {docket_id}")

    def check_dataset(self):
        """
        Checks if any dockets have been inadverently added to the DATA_DIR without being in the dockets core dataset.
        """
        dockets_dir = self.data_dir / 'dockets' / 'data'
        dockets_dir.mkdir(parents=True, exist_ok=True)
        docket_ids = pd.DataFrame({'docket_id':
            [x.name for x in dockets_dir.iterdir()]
        })

        if len(docket_ids):
            batch_size = 100000
            for batch in tqdm(list(partition_all(batch_size, docket_ids.to_dict('records')))):
                self.dataset.add(pd.DataFrame(batch))
        self.dataset.config['last_checked'] = str(datetime.now())

    def __getitem__(self, docket_id):
        return DocketManager(docket_id, data_dir=self.data_dir)
