from copy import deepcopy
from datetime import datetime
import numpy as np
import pandas as pd
from pathlib import Path
import simplejson as json
from toolz import partition_all
from tqdm import tqdm
from docketanalyzer import load_dataset, DocketManager
from docketanalyzer.utils import DATA_DIR


class DocketIndex:
    def __init__(self, data_dir=DATA_DIR, local=False):
        self.data_dir = Path(data_dir)
        self.local = local
        self.cache = {}

    @property
    def dataset(self):
        if 'dataset' not in self.cache:
            self.cache['dataset'] = load_dataset('dockets', pk='docket_id', local=self.local)
        return self.cache['dataset']

    @property
    def header_dataset(self):
        if 'header_dataset' not in self.cache:
            self.cache['header_dataset'] = load_dataset('headers', pk='docket_id', local=self.local)
        return self.cache['header_dataset']

    @property
    def party_dataset(self):
        if 'party_dataset' not in self.cache:
            self.cache['party_dataset'] = load_dataset('parties', pk='party_id', local=self.local)
        return self.cache['party_dataset']

    @property
    def counsel_dataset(self):
        if 'counsel_dataset' not in self.cache:
            self.cache['counsel_dataset'] = load_dataset('counsel', pk='attorney_id', local=self.local)
        return self.cache['counsel_dataset']

    @property
    def judge_dataset(self):
        if 'judge_dataset' not in self.cache:
            self.cache['judge_dataset'] = load_dataset('judges', pk='judge_id', local=self.local)
        return self.cache['judge_dataset']

    @property
    def entry_dataset(self):
        if 'entry_dataset' not in self.cache:
            self.cache['entry_dataset'] = load_dataset('entries', pk='entry_id', local=self.local)
        return self.cache['entry_dataset']

    @property
    def doc_dataset(self):
        if 'doc_dataset' not in self.cache:
            self.cache['doc_dataset'] = load_dataset('docs', pk='doc_id', local=self.local)
        return self.cache['doc_dataset']

    @property
    def idb_dataset(self):
        if 'idb_dataset' not in self.cache:
            self.cache['idb_dataset'] = load_dataset('idb', pk='idb_row', local=self.local)
        return self.cache['idb_dataset']

    @property
    def label_prediction_dataset(self):
        if 'label_prediction_dataset' not in self.cache:
            self.cache['label_prediction_dataset'] = load_dataset('label_predictions', pk='pred_id', local=self.local)
        return self.cache['label_prediction_dataset']
    
    @property
    def label_anno_dataset(self):
        if 'label_anno_dataset' not in self.cache:
            self.cache['label_anno_dataset'] = load_dataset('label_annos', pk='anno_id', local=self.local)
        return self.cache['label_anno_dataset']
    
    @property
    def label_eval_dataset(self):
        if 'label_eval_dataset' not in self.cache:
            self.cache['label_eval_dataset'] = load_dataset('label_evals', pk='eval_id', local=self.local)
        return self.cache['label_eval_dataset']

    @property
    def s3(self):
        if 's3' not in self.cache:
            from docketanalyzer import S3Utility
            self.cache['s3'] = S3Utility(data_dir=self.data_dir)
        return self.cache['s3']

    @property
    def juri(self):
        if 'juri' not in self.cache:
            from docketanalyzer import JuriscraperUtility
            self.cache['juri'] = JuriscraperUtility()
        return self.cache['juri']

    @property
    def ocr(self):
        if 'ocr' not in self.cache:
            from docketanalyzer import OCRUtility
            self.cache['ocr'] = OCRUtility()
        return self.cache['ocr']
    
    @property
    def labels(self):
        if 'labels' not in self.cache:
            from docketanalyzer import load_labels
            self.cache['labels'] = load_labels(index=self)
        return self.cache['labels']

    @property
    def tasks(self):
        if 'tasks' not in self.cache:
            from docketanalyzer import load_tasks
            self.cache['tasks'] = {k: v(dataset=self.dataset) for k, v in load_tasks().items()}
        return self.cache['tasks']

    @property
    def ordered_tasks(self):
        tasks = self.tasks
        visited = {}
        sorted_tasks = []

        def dfs(task):
            visited[task.name] = True
            for dep_name in task.depends_on:
                if dep_name not in visited:
                    dfs(tasks[dep_name])
            sorted_tasks.append(task)

        for task in tasks.values():
            if task.name not in visited:
                dfs(task)

        return sorted_tasks

    @property
    def choices(self):
        if 'choices' not in self.cache:
            from docketanalyzer.choices import choice_registry
            choices = {}
            for name, choice in choice_registry._registry.items():
                choices[name] = {x[0]: x[1] for x in choice.choices()}
            self.cache['choices'] = choices
        return self.cache['choices']

    @property
    def values(self):
        if 'values' not in self.cache:
            choices = deepcopy(self.choices)
            for k in choices:
                choices[k] = {v: k for k, v in choices[k].items()}
            self.cache['values'] = choices
        return self.cache['values']

    def make_batch(self, docket_ids):
        return DocketBatch(docket_ids, self)

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

        if len(self.dataset):
            existing_docket_ids = self.dataset.pandas('docket_id')['docket_id']
            docket_ids = docket_ids[~docket_ids['docket_id'].isin(existing_docket_ids)]

        if len(docket_ids):
            batch_size = 100000
            for batch in tqdm(list(partition_all(batch_size, docket_ids.to_dict('records')))):
                self.dataset.add(pd.DataFrame(batch))
        self.dataset.config['last_checked'] = str(datetime.now())

    def sync(self, path='', delete=False, exact_timestamps=True, exclude=None, push=True, confirm=False):
        path = Path(path)
        try:
            path = path.relative_to(self.data_dir)
        except ValueError:
            pass
        
        if exclude is None:
            exclude = []
        elif isinstance(exclude, str):
            exclude = exclude.split(',')

        exclude.append("*__pycache__*")

        args = dict(
            from_path=path, to_path=path, delete=delete,
            exact_timestamps=exact_timestamps,
            confirm=confirm, exclude=exclude,
        )
        if push:
            self.s3.push(**args)
        else:
            self.s3.pull(**args)
    
    def push(self, path=None, delete=False, exact_timestamps=True, exclude=None, confirm=False):
        self.sync(path, delete, exact_timestamps, exclude, push=True, confirm=confirm)

    def pull(self, path=None, delete=False, exact_timestamps=True, exclude=None, confirm=False):
        self.sync(path, delete, exact_timestamps, exclude, push=False, confirm=confirm)

    def __getitem__(self, docket_id):
        return DocketManager(docket_id, data_dir=self.data_dir, index=self)

    def __iter__(self):
        for docket_id in tqdm(self.dataset.pandas('docket_id')['docket_id']):
            yield self[docket_id]


class DocketBatch:
    def __init__(self, docket_ids, index):
        self.docket_ids = docket_ids
        self.index = index

    @property
    def headers(self):
        choices, values = self.index.choices, self.index.values
        data = []
        for manager in self:
            header = manager.docket_json
            if header:
                header['docket_id'] = manager.docket_id
                del header['parties']
                del header['docket_entries']
                data.append(header)

        def validate(x, valid_items):
            if x not in valid_items:
                raise ValueError(f"Invalid value '{x}'.")

        data = pd.DataFrame(data)
        data = data.rename(columns={'court_id': 'court', 'nature_of_suit': 'nature_suit'})
        data['court'].apply(lambda x: validate(x, choices['DistrictCourt']))
        data['case_type'] = data['docket_number'].apply(lambda x: x.split('-')[1])
        data['case_type'] = data['case_type'].apply(lambda x: x if x in values['CaseType'] else 'other')
        data['nature_suit'] = data['nature_suit'].apply(lambda x: None if not x else '_' + x.split()[0].strip())
        data['nature_suit'].apply(lambda x: None if pd.isnull(x) else validate(x, choices['NatureSuit']))
        data['jury_demand'] = data['jury_demand'].apply(lambda x: None if not x else values['JuryDemand'][x])
        data['jurisdiction'] = data['jurisdiction'].apply(lambda x: None if not x else values['Jurisdiction'][x])
        data['date_filed'] = pd.to_datetime(data['date_filed'], errors='coerce')
        data['date_terminated'] = pd.to_datetime(data['date_terminated'], errors='coerce')

        cols = self.index.header_dataset.columns
        for col in data.columns:
            if cols is not None and col not in cols:
                raise ValueError(f"Column '{col}' not in header columns.")
        return data

    @property
    def parties_and_counsel(self):
        parties, counsel = [], []
        for manager in self:
            docket_json = manager.docket_json
            if docket_json:
                for i, party in enumerate(docket_json['parties']):
                    party_counsel = party.pop('attorneys', [])
                    party_id = f"{manager.docket_id}__{i}"
                    parties.append({
                        'docket_id': manager.docket_id,
                        'party_row': i,
                        'party_id': party_id,
                        **party
                    })
                    for j, attorney in enumerate(party_counsel):
                        counsel.append({
                            'docket_id': manager.docket_id,
                            'party_id': party_id,
                            'attorney_row': j,
                            'attorney_id': f"{manager.docket_id}__{i}__{j}",
                            **attorney
                        })

        parties = pd.DataFrame(parties)
        parties['type'] = parties['type'].apply(lambda x: self.index.values['PartyType'].get(x, 'other'))
        parties['date_terminated'] = pd.to_datetime(parties['date_terminated'], errors='coerce')
        if 'criminal_data' not in parties.columns:
            parties['criminal_data'] = None
        parties.loc[parties['criminal_data'].notnull(), 'criminal_data'] = (
            parties[parties['criminal_data'].notnull()]['criminal_data'].apply(json.dumps)
        )

        counsel = pd.DataFrame(counsel)
        counsel['roles'] = counsel['roles'].apply(json.dumps)

        cols = self.index.party_dataset.columns
        for col in parties.columns:
            if cols is not None and col not in cols:
                raise ValueError(f"Column '{col}' not in party columns.")

        cols = self.index.counsel_dataset.columns
        for col in counsel.columns:
            if cols is not None and col not in cols:
                raise ValueError(f"Column '{col}' not in counsel columns.")
        return parties, counsel

    def get_entries(self, add_shuffle_number=False):
        data = []
        for manager in self:
            docket_json = manager.docket_json
            if docket_json:
                entries = pd.DataFrame(docket_json['docket_entries'])
                if len(entries):
                    entries['docket_id'] = manager.docket_id
                    entries['row_number'] = range(len(entries))
                    if add_shuffle_number:
                        entries['shuffle_number'] = np.random.permutation(len(entries))
                    data.append(entries)
        if not len(data):
            return None
        data = pd.concat(data)
        data['entry_id'] = data.apply(lambda x: f"{x['docket_id']}__{x['row_number']}", axis=1)
        data['date_filed'] = pd.to_datetime(data['date_filed'], errors='coerce')
        data['pacer_doc_id'] = data['pacer_doc_id'].astype(pd.Int64Dtype())
        data['document_number'] = data['document_number'].astype(pd.Int64Dtype())
        data['pacer_seq_no'] = data['pacer_seq_no'].astype(pd.Int64Dtype())
        data['date_entered'] = pd.to_datetime(data['date_entered'], errors='coerce')

        cols = self.index.entry_dataset.columns
        for col in data.columns:
            if cols is not None and col not in cols:
                raise ValueError(f"Column '{col}' not in entry columns.")
        return data

    @property
    def entries(self):
        return self.get_entries()

    def __iter__(self):
        for docket_id in self.docket_ids:
            yield self.index[docket_id]


def load_docket_index(*args, **kwargs):
    return DocketIndex(*args, **kwargs)
