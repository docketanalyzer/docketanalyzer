from datetime import datetime
from tqdm import tqdm
from docketanalyzer import Registry, load_docket_index


class Task:
    name = None
    batch_size = None
    depends_on = []
    data_cols = []
    inactive = False

    def __init__(self, index, selected_ids=None):
        self.index = index
        self.cache = {}
        self.selected_ids = selected_ids
        self.init_columns()

    @property
    def table(self):
        return self.index.table

    def init_columns(self):
        self.table.add_column(self.status_col_name, 'DateTimeField')
        for depends_on in self.depends_on:
            status_col_name = self.get_status_col_name(depends_on)
            self.table.add_column(status_col_name, 'DateTimeField')
        for col in self.data_cols:
            self.table.add_column(**col)

    def get_status_col_name(self, name):
        return f"task_{name.replace('-', '_').replace(' ', '_')}"

    @property
    def status_col_name(self):
        return self.get_status_col_name(self.name)
    
    @property
    def status_col(self):
        return getattr(self.table, self.status_col_name)

    @property
    def progress(self):
        total = self.table.count()
        complete = self.table.where(self.status_col.is_null(False)).count()
        pct = 0 if not total else complete / total
        return total, complete, pct

    @property
    def progress_str(self):
        total, complete, pct = self.progress
        return f"{pct:.2%} ({complete} / {total})"

    @property
    def q(self):
        query = self.initial_query()
        if self.selected_ids:
            query = query.where(self.index.table_id_col.in_(self.selected_ids))
        return query

    def set_selected_ids(self, selected_ids):
        if selected_ids is not None:
            self.selected_ids = selected_ids

    def reset(self, selected_ids=None, quiet=False):
        self.set_selected_ids(selected_ids)
        if self.selected_ids:
            self.table.update({self.status_col: None}).where(self.q._where).execute()
        else:
            self.table.drop_column(self.status_col_name, confirm=not quiet)
            self.table.add_column(self.status_col_name, 'DateTimeField')
        self.post_reset()

    def delete(self, confirm=True):
        self.table.drop_column(self.status_col_name, confirm=confirm)
        for col in self.data_cols:
            self.table.drop_column(col['column_name'])

    def run(self, selected_ids=None):
        self.set_selected_ids(selected_ids)

        print(f"Running {self.name}")
        status_col = self.status_col
        for depends_on in self.depends_on:
            depends_on_col_name = self.get_status_col_name(depends_on)
            depends_on_col = getattr(self.table, depends_on_col_name)
            condition = (status_col <= depends_on_col) | (depends_on_col.is_null(True))
            self.table.update({status_col: None}).where(condition).execute()
        
        condition = status_col.is_null(True)
        for depends_on in self.depends_on:
            depends_on_col_name = self.get_status_col_name(depends_on)
            depends_on_col = getattr(self.table, depends_on_col_name)
            condition &= depends_on_col.is_null(False)
        query = self.q.where(condition)

        done = True
        if query.count():
            done = False
            self.prepare()
            for batch in query.batch(self.batch_size):
                self.run_batch(batch)
        return done

    def run_batch(self, batch):
        batch_ids = batch.pandas(self.index.table_id_col_name)[self.index.table_id_col_name].tolist()
        self.process(batch)
        self.table.update({self.status_col: datetime.now()}).where(self.index.table_id_col.in_(batch_ids)).execute()

    def post_reset(self):
        pass

    def initial_query(self):
        return self.table.select(self.table)

    def prepare(self):
        pass

    def process_row(self, row):
        raise NotImplementedError("task.process or task.process_row must be implemented.")

    def process(self, batch):
        for row in batch:
            self.process_row(row)


class DocketTask(Task):
    def __init__(self, index=None, selected_ids=None):
        if index is None:
            index = load_docket_index()
        super().__init__(index, selected_ids)


class TaskRegistry(Registry):
    def find_filter(self, obj):
        return (
            isinstance(obj, type) and
            issubclass(obj, Task) and
            obj is not Task and
            obj.name is not None and 
            obj.inactive is False
        )


task_registry = TaskRegistry()


def load_tasks():
    return {x.name: x for x in task_registry.all()}


def load_task(name):
    for task in task_registry.all():
        if task.name == name:
            return task


def register_task(task_class):
    task_registry.register(task_class.__name__, task_class)
