from datetime import datetime
import urllib.parse
import django
from django.db import models
from django.conf import settings
from django.core.management.commands.inspectdb import Command as InspectDB
from django.core.paginator import Paginator
import pandas as pd
from sqlalchemy import (
    create_engine, Table, Column,
    MetaData, select, insert, update, DDL,
    Integer, String, DateTime, Float, Boolean
)
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import (
    OperationalError, NoSuchTableError,
    ProgrammingError,
)
from toolz import partition_all
from tqdm import tqdm
from docketanalyzer.utils import (
    DATA_DIR, POSTGRES_DB, POSTGRES_HOST,
    POSTGRES_PASSWORD, POSTGRES_PORT,
    POSTGRES_USERNAME,
)


class CoreDatasetConfig:
    def __init__(self, dataset_name, engine):
        self.dataset_name = dataset_name
        self.engine = engine
        self.metadata = MetaData()
        self.table = Table(
            'config', self.metadata,
            Column('dataset', String, primary_key=True),
            Column('key', String, primary_key=True),
            Column('value', String)
        )
        self.metadata.create_all(self.engine)

    def __getitem__(self, key):
        with self.engine.connect() as conn:
            s = select(self.table).where(
                self.table.c.dataset == self.dataset_name,
                self.table.c.key == key,
            )
            result = conn.execute(s).fetchone()
            if result:
                return result.value
            else:
                raise KeyError(f"Key {key} not found.")

    def __setitem__(self, key, value):
        with self.engine.connect() as conn:
            with conn.begin():
                s = select(self.table).where(
                    self.table.c.dataset == self.dataset_name,
                    self.table.c.key == key,
                )
                result = conn.execute(s).fetchone()
                if result:
                    stmt = update(self.table).where(
                        self.table.c.dataset == self.dataset_name,
                        self.table.c.key == key,
                    ).values(value=value)
                else:
                    stmt = insert(self.table).values(
                        dataset=self.dataset_name,
                        key=key, value=value,
                    )
                conn.execute(stmt)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def delete(self, key=None):
        with self.engine.connect() as conn:
            with conn.begin():
                stmt = self.table.delete().where(self.table.c.dataset == self.dataset_name)
                if key:
                    stmt = stmt.where(self.table.c.key == key)
                conn.execute(stmt)


class CoreDatasetQuerySet(models.QuerySet):
    def pandas(self, *columns):
        return pd.DataFrame(list(self.values(*columns)))

    def sample(self, n):
        return self.order_by('?')[:n]

    def get_first_as_dict(self, *args, **kwargs):
        return self.filter(*args, **kwargs).values().first()

    def page(self, page_number=1, results_per_page=100):
        queryset = self
        if not self.query.order_by:
            queryset = queryset.order_by('id')
        paginator = Paginator(queryset, results_per_page)
        return paginator.get_page(page_number)

    def batch(self, batch_size):
        queryset = self
        if not self.query.order_by:
            queryset = queryset.order_by('id')
        ids = list(queryset.values_list('id', flat=True))
        for batch_ids in tqdm(list(partition_all(batch_size, ids))):
            yield queryset.filter(id__in=batch_ids)


class CoreDatasetModelManager(models.Manager):
    def get_queryset(self):
        return CoreDatasetQuerySet(self.model, using=self._db)


class CoreDataset:
    def __init__(self, name, pk=None, local=False, connect_args={}):
        if pk == 'id':
            raise ValueError("Cannot use 'id' as a primary key")
        if name == 'config':
            raise ValueError("Cannot use 'config' as a dataset name")
        self.name = name
        self.local = local
        self.connect_args = connect_args
        self.engine = self.connect()
        self.config = CoreDatasetConfig(name, self.engine)
        self.cache = {}
        if pk:
            self.config['pk'] = pk

    @property
    def pk(self):
        if 'pk' not in self.cache:
            pk = self.config.get('pk')
            if not pk:
                raise ValueError(f"Primary key not set. You must initialize your dataset with CoreDataset({self.name}, pk=...) or load_dataset({self.name}, pk=...) at least once before certain functionality can be used.")
            self.cache['pk'] = pk.lower()
        return self.cache['pk']

    @property
    def columns(self):
        metadata = MetaData()
        try:
            table = Table(self.name, metadata, autoload_with=self.engine)
            return [column.name for column in table.columns]
        except NoSuchTableError:
            return None

    def connect(self):
        if POSTGRES_HOST and not self.local:
            engine = create_engine(
                URL.create(
                    drivername="postgresql",
                    username=POSTGRES_USERNAME,
                    password=POSTGRES_PASSWORD,
                    host=POSTGRES_HOST,
                    port=POSTGRES_PORT,
                    database=POSTGRES_DB,
                ),
                connect_args=self.connect_args
            )
            return engine
        else:
            (DATA_DIR / 'local').mkdir(exist_ok=True, parents=True)
            url = f"sqlite:///{DATA_DIR / 'local' / 'db.sqlite3'}"
            return create_engine(url)

    def setup_django(self):
        if not settings.configured:
            if POSTGRES_HOST and not self.local:
                database = {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': POSTGRES_DB,
                    'USER': POSTGRES_USERNAME,
                    'PASSWORD': POSTGRES_PASSWORD,
                    'HOST': POSTGRES_HOST,
                    'PORT': POSTGRES_PORT,
                }
            else:
                database = {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': DATA_DIR / 'local' / 'db.sqlite3',
                }

            settings.configure(
                DATABASES={'default': database},
                INSTALLED_APPS=['docketanalyzer.app.data'],
                USE_TZ=False,
            )
            django.setup()

    @property
    def django_model_name(self):
        return f"{self.name.capitalize()}DjangoModel"

    @property
    def django_model(self):
        if not self.cache.get('django_model'):
            self.pk
            self.setup_django()
            if self.django_model_name not in globals():
                db_schema = list(InspectDB().handle_inspection({
                    'database': 'default',
                    'table': [self.name],
                    'include_partitions': False,
                    'include_views': False,
                }))
                db_schema = '\n'.join(db_schema[db_schema.index('from django.db import models') + 4:])
                if len(db_schema.strip()):
                    db_schema = f'class {self.django_model_name}(models.Model):\n' + db_schema
                    db_schema += '\n        app_label = "docketanalyzer.app.data"'
                    db_schema += '\n\n    objects = CoreDatasetModelManager()'
                    exec(db_schema, globals())
            self.cache['django_model'] = globals().get(self.django_model_name)
        return self.cache['django_model']

    def reload_django_model(self):
        self.cache.pop('django_model', None)
        if self.django_model_name in globals():
            del globals()[self.django_model_name]

    @property
    def q(self):
        return self.get_queryset()

    def get_queryset(self):
        return self.django_model.objects.all()

    def add_column(self, column_name, column_type):
        type_mapping = {
            int: Integer,
            str: String,
            float: Float,
            bool: Boolean,
            datetime: DateTime,
            'int': Integer,
            'str': String,
            'float': Float,
            'bool': Boolean,
            'datetime': DateTime,
        }
        column_type = type_mapping.get(column_type, column_type)()
        with self.engine.connect() as conn:
            column_definition = f"{column_name} {column_type.compile(dialect=self.engine.dialect)}"
            sql = DDL(f"ALTER TABLE {self.name} ADD COLUMN {column_definition}")
            with conn.begin():
                conn.execute(sql)
        self.reload_django_model()

    def drop_column(self, column_name):
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(DDL(f'ALTER TABLE {self.name} DROP COLUMN {column_name}'))
        self.reload_django_model()

    def delete(self, quiet=False):
        if not quiet:
            confirm = input(f"Are you sure you want to delete the dataset {self.name}? (y/n) ")
            if confirm.lower() != 'y':
                return
        self.config.delete()
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(DDL(f'DROP TABLE IF EXISTS {self.name}'))

    def add(self, data, verbose=True):
        pk = self.pk
        columns = self.columns

        if any(not col.islower() for col in data.columns):
            data.columns = [col.lower() for col in data.columns]
            print("Warning: Column names must be lowercase. Converting to lowercase.")

        data = data.drop_duplicates(subset=[pk])

        if 'id' in data.columns:
            data = data.drop(columns=['id'])
            print("Warning: 'id' column is reserved. Removing from dataset.")

        if columns is not None:
            missing_cols = [x for x in self.columns if x not in data.columns]
            for col in missing_cols:
                data[col] = None
            dropped_cols = [x for x in data.columns if x not in self.columns]
            if dropped_cols:
                print(f"Warning: We are removing the following columns as they are not in the existing data: {dropped_cols}")
            data = data[columns]

        total_records = len(self)
        if total_records:
            ids = self.all().values_list(pk, flat=True)
            data = data[~data[pk].isin(ids)]

        if len(data):
            if columns is None or 'id' not in columns:
                start_id = 0
            else:
                start_id = self.q.aggregate(models.Max('id'))['id__max'] + 1 or 0

            data['id'] = range(start_id, start_id + len(data))
            data.to_sql(self.name, self.engine, if_exists='append', index=False, dtype={
                pk: String(128), 'id': Integer(),
            })
            if start_id == 0:
                with self.engine.connect() as conn:
                    with conn.begin():
                        sql = f"ALTER TABLE {self.name} ADD PRIMARY KEY ({self.pk})"
                        conn.execute(DDL(sql))

        if verbose:
            print(f"Added {len(data)} records to dataset. Total records: {len(self)}")

    def all(self):
        return self.q

    def get(self, *args, **kwargs):
        return self.q.get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        return self.q.filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        return self.q.exclude(*args, **kwargs)

    def values(self, *args, **kwargs):
        return self.q.values(*args, **kwargs)

    def sample(self, *args, **kwargs):
        return self.q.sample(*args, **kwargs)

    def pandas(self, *args, **kwargs):
        return self.q.pandas(*args, **kwargs)

    def page(self, *args, **kwargs):
        return self.q.page(*args, **kwargs)

    def batch(self, *args, **kwargs):
        return self.q.batch(*args, **kwargs)

    def count(self, *args, **kwargs):
        return self.q.count(*args, **kwargs)

    def __getitem__(self, key):
        args = {self.pk: key}
        return self.get(**args)

    def __iter__(self):
        return iter(tqdm(self.all(), total=len(self)))

    def __len__(self):
        django_model = self.django_model
        if django_model:
            return django_model.objects.count()
        else:
            return 0


def load_dataset(*args, **kwargs):
    return CoreDataset(*args, **kwargs)
