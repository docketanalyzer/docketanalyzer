import os
import django
from django.db import models
from django.conf import settings
from django.core.management.commands.inspectdb import Command as InspectDB
import pandas as pd
from sqlalchemy import (
    create_engine, Table, Column, Integer,
    String, MetaData, select, insert, update, DDL
)
from sqlalchemy.exc import (
    OperationalError, NoSuchTableError,
    ProgrammingError,
)
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
            transaction = conn.begin()
            try:
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
                transaction.commit()
            except:
                transaction.rollback()
                raise

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def delete(self, key=None):
        with self.engine.connect() as conn:
            try:
                transaction = conn.begin()
                stmt = self.table.delete().where(self.table.c.dataset == self.dataset_name)
                if key:
                    stmt = stmt.where(self.table.c.key == key)
                conn.execute(stmt)
                transaction.commit()
            except:
                transaction.rollback()
                raise


class CoreDatasetModelManager(models.Manager):
    def to_pandas(self, *columns):
        queryset = self.get_queryset()
        return pd.DataFrame(list(queryset.values(*columns)))

    def sample(self, n, *columns):
        queryset = self.get_queryset().order_by('?')
        return pd.DataFrame(queryset.values(*columns)[:n])

    def get(self, *args, **kwargs):
        return self.get_queryset().filter(*args, **kwargs).values().first()


class CoreDataset:
    def __init__(self, name, pk=None, local=False):
        if pk == 'id':
            raise ValueError("Cannot use 'id' as a primary key")
        if name == 'config':
            raise ValueError("Cannot use 'config' as a dataset name")
        self.name = name
        self.local = local
        self.engine = self.connect()
        self.config = CoreDatasetConfig(name, self.engine)
        self.django_setup = False
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
            url = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        else:
            (DATA_DIR / 'local').mkdir(exist_ok=True, parents=True)
            url = f"sqlite:///{DATA_DIR / 'local' / 'db.sqlite3'}"
        return create_engine(url)

    def setup_django(self):
        if not self.django_setup:
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
                INSTALLED_APPS=['docketanalyzer.app.data']
            )
            django.setup()
            self.django_setup = True

    @property
    def django_model_name(self):
        return f"{self.name.capitalize()}DjangoModel"

    @property
    def django_model(self):
        if 'django_model' not in self.cache:
            self.pk
            self.setup_django()
            db_schema = list(InspectDB().handle_inspection({
                'database': 'default',
                'table': [self.name],
                'include_partitions': False,
                'include_views': False,
            }))
            db_schema = '\n'.join(db_schema[db_schema.index('from django.db import models') + 4:])
            db_schema = f'class {self.django_model_name}(models.Model):\n' + db_schema
            db_schema += '\n        app_label = "docketanalyzer.app.data"'
            db_schema += '\n\n    objects = CoreDatasetModelManager()'

            exec(db_schema, globals())
            self.cache['django_model'] = globals()[self.django_model_name]
        return self.cache['django_model']

    def add_column(self, column_name, column_type):
        with self.engine.connect() as conn:
            conn.execute(DDL(f'ALTER TABLE {self.name} ADD COLUMN {column_name} {column_type}'))
        self.cache.pop('django_model', None)

    def drop_column(self, column_name):
        with self.engine.connect() as conn:
            conn.execute(DDL(f'ALTER TABLE {self.name} DROP COLUMN {column_name}'))
        self.cache.pop('django_model', None)

    def delete(self, quiet=False):
        if not quiet:
            confirm = input(f"Are you sure you want to delete the dataset {self.name}? (y/n) ")
            if confirm.lower() != 'y':
                return
        self.config.delete()
        with self.engine.connect() as conn:
            conn.execute(DDL(f'DROP TABLE IF EXISTS {self.name}'))

    def add(self, data, verbose=True):
        pk = self.pk
        columns = self.columns

        if any(not col.islower() for col in data.columns):
            data.columns = [col.lower() for col in data.columns]
            print("Warning: Column names must be lowercase. Converting to lowercase.")

        data = data.drop_duplicates(subset=[pk])

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
            ids = pd.read_sql_query(f"SELECT {pk} FROM {self.name}", self.engine)
            data = data[~data[pk].isin(ids[pk])]

        if len(data):
            start_id = total_records
            data['id'] = range(start_id, start_id + len(data))
            data.to_sql(self.name, self.engine, if_exists='append', index=False, dtype={
                'id': Integer,
                pk: String(128),
            })
        if verbose:
            print(f"Added {len(data)} records to dataset. Total records: {len(self)}")

    def __len__(self):
        try:
            return pd.read_sql_query(f"SELECT COUNT(*) FROM {self.name}", self.engine).iloc[0, 0]
        except (OperationalError, ProgrammingError):
            return 0

    def all(self):
        return self.django_model.objects.all()

    def get(self, *args, **kwargs):
        return self.django_model.objects.get(*args, **kwargs)

    def filter(*args, **kwargs):
        return self.django_model.objects.filter(*args, **kwargs)

    def exclude(*args, **kwargs):
        return self.django_model.objects.exclude(*args, **kwargs)

    def values(self, *args, **kwargs):
        return self.django_model.objects.values(*args, **kwargs)

    def sample(self, *args, **kwargs):
        return self.django_model.objects.sample(*args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        return self.django_model.objects.to_pandas(*args, **kwargs)

    def __getitem__(self, key):
        args = {self.pk: key}
        return self.get(**args)


def load_dataset(*args, **kwargs):
    return CoreDataset(*args, **kwargs)
