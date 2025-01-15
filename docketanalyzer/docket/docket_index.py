from copy import deepcopy
import pandas as pd
from toolz import partition_all
from tqdm import tqdm
from docketanalyzer import ObjectIndex
from .choices import choice_registry
from .docket_manager import DocketManager
from .docket_batch import DocketBatch


class DocketIndex(ObjectIndex):
    name = 'dockets'
    id_col = dict(column_name='docket_id', column_type='CharField')
    manager_class = DocketManager
    batch_class = DocketBatch

    @property
    def choices(self):
        if 'choices' not in self.cache:
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

    def check_docket_dirs(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        docket_ids = pd.DataFrame({'docket_id': [
            x.name for x in self.dir.iterdir()
            if x.is_dir() and not x.name.startswith('.')
        ]})

        if self.table.count():
            existing_docket_ids = self.table.pandas('docket_id')['docket_id']
            docket_ids = docket_ids[~docket_ids['docket_id'].isin(existing_docket_ids)]

        if len(docket_ids):
            batch_size = 100000
            for batch in tqdm(list(partition_all(batch_size, docket_ids.to_dict('records')))):
                self.table.add_data(pd.DataFrame(batch), copy=True)

    @property
    def juri(self):
        if 'juri' not in self.cache:
            try:
                from docketanalyzer import JuriscraperUtility
            except ImportError:
                raise ImportError("JuriscraperUtility is not available. Please install the 'docketanalyzer[flp]' extension.")
            self.cache['juri'] = JuriscraperUtility()
        return self.cache['juri']

    def add_from_html(self, html, docket_id=None, court=None, skip_duplicates=True, add_to_index=True):
        if docket_id is None:
            if court is None:
                raise ValueError("Either docket_id or court must be provided.")
            docket_parsed = self.juri.parse(html, court)
            docket_id = f"{docket_parsed['court_id']}__{docket_parsed['docket_number'].replace(':', '_')}"
        print(f"Docket ID identified: {docket_id}")
        manager = self[docket_id]
        manager.add_docket_html(html, skip_duplicates=skip_duplicates, add_to_index=add_to_index)
        return manager

    @property
    def tasks(self):
        if 'tasks' not in self.cache:
            from docketanalyzer import load_tasks
            self.cache['tasks'] = {k: v(self) for k, v in load_tasks().items()}
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


def load_docket_index(*args, **kwargs):
    return DocketIndex(*args, **kwargs)
