from pathlib import Path
import pandas as pd
import peewee as pw
from tqdm import tqdm
from docketanalyzer import env
from .psql import load_psql


class ObjectManager:
    batch_attributes = []

    def __init__(self, id, index):
        self.id = id
        self.index = index
        self.cache = {}

    def get_path(self):
        return self.index.dir / self.id

    @property
    def path(self):
        return self.get_path()

    @property
    def dir(self):
        if not self.path.suffix:
            return self.path
    
    @property
    def db(self):
        return self.index.db

    @property
    def t(self):
        return self.index.t
    
    @property
    def table(self):
        return self.index.table

    @property
    def row(self):
        return self.index.table.where(self.index.table_id_col == self.id).first()

    def add_to_index(self):
        try:
            if self.index.cached_ids_path.exists():
                self.index.cached_ids_path.unlink()
            self.table.insert({self.index.table_id_col_name: self.id}).execute()
        except pw.IntegrityError:
            pass

    def push(self, name=None, **kwargs):
        if name is not None:
            kwargs['exclude'] = '*'
            kwargs['include'] = name
        self.index.push(self.path, **kwargs)
    
    def pull(self, name=None, **kwargs):
        if name is not None:
            kwargs['exclude'] = '*'
            kwargs['include'] = name
        self.index.pull(self.path, **kwargs)

    @property
    def batch(self):
        return self.index.make_batch([self.id])

    def __getattribute__(self, name):
        if name in object.__getattribute__(self, 'batch_attributes'):
            return getattr(object.__getattribute__(self, 'batch'), name)
        return object.__getattribute__(self, name)
    

class ObjectBatch:
    def __init__(self, obj_ids, index):
        self.obj_ids = obj_ids
        self.index = index
        self.cache = {}

    @property
    def db(self):
        self.index.db

    @property
    def t(self):
        return self.index.t

    @property
    def table(self):
        self.index.table
    
    def __iter__(self):
        for obj_id in self.obj_ids:
            yield self.index[obj_id]


class ObjectIndex:
    name = None
    id_col = dict(column_name='id')
    manager_class = ObjectManager
    batch_class = ObjectBatch

    def __init__(self, data_dir=None, db_connection={}):
        data_dir = data_dir or env.DATA_DIR
        self.data_dir = Path(data_dir)
        self.dir = self.data_dir / 'data' / self.name
        self.db_connection = db_connection
        self.cache = {}

    @property
    def table_name(self):
        return f"{self.name}_index"

    @property
    def db(self):
        if 'db' not in self.cache:
            self.cache['db'] = load_psql(**self.db_connection)
        return self.cache['db']
    
    @property
    def t(self):
        return self.db.t

    @property
    def table(self):
        if 'table' not in self.cache:
            self.db.create_table(self.table_name)
            table = self.db.t[self.table_name]
            id_col = self.id_col.copy()
            if id_col['column_name'] != 'id':
                if 'unique' not in self.id_col:
                    id_col['unique'] = True
                table.add_column(**id_col)
            self.cache['table'] = table
        return self.cache['table']

    @property
    def table_id_col_name(self):
        return self.id_col['column_name']

    @property
    def table_id_col(self):
        return getattr(self.table, self.table_id_col_name)

    @property
    def cached_ids_path(self):
        return self.dir / 'ids.csv'

    def load_cached_ids(self, shuffle=False):
        if not self.cached_ids_path.exists():
            obj_ids = self.table.pandas(self.table_id_col_name)
            obj_ids.to_csv(self.cached_ids_path, index=False)
        obj_ids = pd.read_csv(self.cached_ids_path)[self.table_id_col_name]
        if shuffle:
            obj_ids = obj_ids.sample(frac=1)
        return obj_ids.tolist()

    def reset_cached_ids(self):
        if self.cached_ids_path.exists():
            self.cached_ids_path.unlink()
    
    @property
    def cached_ids(self):
        return self.load_cached_ids()

    @property
    def s3(self):
        if 's3' not in self.cache:
            from docketanalyzer import S3
            self.cache['s3'] = S3(data_dir=self.data_dir)
        return self.cache['s3']
    
    def push(self, path='', confirm=False, **args):
        self.s3.push(path=path, confirm=confirm, **args)

    def pull(self, path='', confirm=False, **args):
        self.s3.pull(path=path, confirm=confirm, **args)

    def make_batch(self, obj_ids):
        return self.batch_class(obj_ids, self)

    def __getitem__(self, obj_id):
        return self.manager_class(obj_id, index=self)

    def __iter__(self):
        for obj_id in tqdm(self.load_cached_ids()):
            yield self[obj_id]
