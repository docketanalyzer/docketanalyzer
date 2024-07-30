from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db.models import F, Q
from django.utils import timezone
import pandas as pd
from tqdm import tqdm
from docketanalyzer import load_dataset, load_docket_index


class Task:
    name = None
    batch_size = None
    dataset_args = {}
    depends_on = []
    data_cols = []
    workers = None
    inactive = False

    def __init__(self, dataset=None, selected_ids=None, **kwargs):
        if dataset is None:
            dataset_args = self.dataset_args.copy()
            dataset_args.update(kwargs)
            dataset = load_dataset(**dataset_args)
        self.dataset = dataset
        self.cache = {}
        self.init_columns()
        self.selected_ids = selected_ids

    def init_columns(self):
        columns = self.dataset.columns
        if self.last_updated_col not in columns:
            self.dataset.add_column(self.last_updated_col, 'datetime')
        for depends_on in self.depends_on:
            status_col = self.get_last_updated_col(depends_on)
            if status_col not in columns:
                self.dataset.add_column(status_col, 'datetime')
        for col in self.data_cols:
            if col[0] not in columns:
                self.dataset.add_column(*col)

    def get_last_updated_col(self, name):
        return f"status_{name.replace('-', '_').replace(' ', '_')}_last_updated"

    @property
    def last_updated_col(self):
        return self.get_last_updated_col(self.name)

    @property
    def progress(self):
        total = self.q.count()
        complete = self.dataset.filter(**{f"{self.last_updated_col}__isnull": False}).count()
        pct = 0 if not total else complete / total
        return total, complete, pct

    @property
    def progress_str(self):
        total, complete, pct = self.progress
        return f"{pct:.2%} ({complete} / {total})"

    @property
    def q(self):
        query = self.get_queryset()
        if self.selected_ids:
            query = query.filter(**{self.dataset.pk + '__in': self.selected_ids})
        return query
    
    def post_reset(self, selected_ids):
        pass

    def reset(self, data=True, init=True, selected_ids=None):
        if selected_ids is not None:
            self.selected_ids = selected_ids
        if self.selected_ids:
            self.q.update(**{self.last_updated_col: None})
        else:
            print(f"Deleting task data: {self.name}")
            if self.last_updated_col in self.dataset.columns:
                self.dataset.drop_column(self.last_updated_col)
            if data:
                for col in self.data_cols:
                    if col[0] in self.dataset.columns:
                        self.dataset.drop_column(col[0])
            if init:
                print(f"Reinitializing task data: {self.name}")
                self.init_columns()
        self.post_reset(self.selected_ids)

    def delete(self):
        self.reset(init=False)

    def run_batch(self, batch):
        batch_ids = batch.pandas(self.dataset.pk)[self.dataset.pk].tolist()
        self.process(batch)
        self.dataset.filter(
            **{self.dataset.pk + '__in': batch_ids}
        ).update(**{self.last_updated_col: timezone.now()})

    def run(self, selected_ids=None):
        if selected_ids is not None:
            self.selected_ids = selected_ids

        print(f"Running {self.name}")
        for depends_on in self.depends_on:
            status_col = self.get_last_updated_col(depends_on)
            self.dataset.filter(
                Q(**{f"{self.last_updated_col}__lte": F(status_col)}) |
                Q(**{f"{status_col}__isnull": True})
            ).update(
                **{self.last_updated_col: None}
            )
        query = self.q.filter(**{f"{self.last_updated_col}__isnull": True})
        for depends_on in self.depends_on:
            status_col = self.get_last_updated_col(depends_on)
            query = query.filter(
                **{f"{status_col}__isnull": False}
            )
        done = True
        if query.count():
            done = False
            total = 0
            self.prepare()
            if self.workers is None:
                for batch in query.batch(self.batch_size):
                    total += len(batch)
                    self.run_batch(batch)
            else:
                with ThreadPoolExecutor(max_workers=self.workers) as executor:
                    futures = []
                    for batch in query.batch(self.batch_size):
                        total += len(batch)
                        futures.append(executor.submit(self.run_batch, batch))

                    for future in tqdm(as_completed(futures), total=len(futures)):
                        pass

        return done

    def prepare(self):
        pass

    def get_queryset(self):
        return self.dataset.all()

    def process_row(self, row):
        raise NotImplementedError("task.process or task.process_row must be implemented.")

    def process(self, batch):
        for row in batch:
            self.process_row(row)


class DocketTask(Task):
    dataset_args = dict(name='dockets')

    @property
    def index(self):
        if 'index' not in self.cache:
            self.cache['index'] = load_docket_index(local=self.dataset.local)
        return self.cache['index']
