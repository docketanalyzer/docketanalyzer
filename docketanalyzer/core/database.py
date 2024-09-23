import csv
from datetime import datetime
from io import StringIO
from urllib.parse import urlparse
import pandas as pd
import peewee
from peewee import (
    Model, CharField, DateTimeField,
    ForeignKeyField, ModelSelect,
)
from playhouse.migrate import migrate, PostgresqlMigrator
from playhouse.postgres_ext import PostgresqlExtDatabase, JSONField
from playhouse.reflection import Introspector
from playhouse.shortcuts import model_to_dict
from toolz import partition_all
from tqdm import tqdm
from docketanalyzer import (
    POSTGRES_URL,
    require_confirmation_wrapper, require_confirmation, notabs,
)


class CustomQueryMixin:
    def pandas(self, *columns, copy=False):
        if columns:
            columns = [getattr(self.model, col) for col in columns]
            query = self.select(*columns)
        else:
            query = self

        if copy:
            conn = self.model._meta.database.connection()
            with conn.cursor() as cursor:
                sql, params = query.sql()
                params = tuple(params) if isinstance(params, list) else params
                copy_sql = cursor.mogrify(
                    f"COPY ({sql}) TO STDOUT WITH CSV HEADER", 
                    params,
                ).decode('utf-8')
                buffer = StringIO()
                cursor.copy_expert(copy_sql, buffer)
                buffer.seek(0)
                data = pd.read_csv(buffer)
        else:
            data = pd.DataFrame(list(query.dicts()))

        return data

    def sample(self, n):
        return self.order_by(peewee.fn.Random()).limit(n)

    def delete(self):
        model_class = self.model
        subquery = self.select(model_class._meta.primary_key)
        delete_query = model_class.delete().where(
            model_class._meta.primary_key.in_(subquery)
        )
        return delete_query.execute()

    def batch(self, n, verbose=True):
        model_class = self.model
        pk_field = model_class._meta.primary_key
        query = self.clone()
        query = query.order_by(pk_field)
        total, progress = None, None

        if verbose:
            total = query.count()
            progress = tqdm(total=total)

        last_id, processed = None, 0
        while True:
            if last_id is not None:
                batch_query = query.where(pk_field > last_id)
            else:
                batch_query = query

            batch = batch_query.limit(n)
            if not batch:
                break
            yield batch

            last_id = getattr(batch[-1], pk_field.name)
            processed += len(batch)
            if verbose:
                progress.update(len(batch))
        if verbose:
            progress.close()


class CustomModelSelect(ModelSelect, CustomQueryMixin):
    pass


class CustomModelQueryMixin:
    @classmethod
    def select(cls, *fields):
        is_default = not fields
        if not fields:
            fields = cls._meta.sorted_fields
        return CustomModelSelect(cls, fields, is_default=is_default)

    @classmethod
    def sample(cls, n):
        return cls.select(cls).sample(n)
    
    @classmethod
    def pandas(cls, *columns, copy=False):
        return cls.select(cls).pandas(*columns, copy=copy)

    @classmethod
    def where(cls, *args, **kwargs):
        return cls.select(cls).where(*args, **kwargs)

    @classmethod
    def batch(cls, n, verbose=False):
        return cls.select(cls).batch(n, verbose=verbose)
    
    @classmethod
    def count(cls):
        return cls.select().count()

    def dict(self):
        return model_to_dict(self)


class CustomModel(CustomModelQueryMixin, Model):
    db_manager = None

    @classmethod
    @require_confirmation_wrapper(
        message=lambda args: notabs(f"""
            Are you sure you want to drop column '{args['column_name']}' from '{args['cls']._meta.table_name}'?
            This will DELETE ALL COLUMN DATA.
        """),
        disable=lambda args: not args.get('confirm', True),
    )
    def drop_column(cls, column_name, confirm=True):
        table_name = cls._meta.table_name
        migrator = PostgresqlMigrator(cls._meta.database)
        migrate(migrator.drop_column(table_name, column_name))
        cls.reload()

    @classmethod
    def add_column(cls, column_name, column_type, null=None, overwrite=False, exists_ok=True, **kwargs):
        table_name = cls._meta.table_name
        table_meta = cls.db_manager.meta[table_name]
        migrator = PostgresqlMigrator(cls._meta.database)
        if column_name in table_meta['columns']:
            if not exists_ok:
                raise ValueError(f'Column {column_name} already exists in table {table_name}.')
            if not overwrite:
                return
            cls.drop_column(column_name)

        if null is None:
            null = True if 'default' not in kwargs else False
        kwargs['null'] = null
        migrate(
            migrator.add_column(table_name, column_name, getattr(peewee, column_type)(**kwargs))
        )
        cls.reload()
    
    @classmethod
    def add_data(cls, data, copy=False, batch_size=1000):
        if copy:
            conn = cls._meta.database.connection()
            with conn.cursor() as cursor:
                    buffer = StringIO()
                    csv_writer = csv.writer(buffer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    for _, row in data.iterrows():
                        csv_writer.writerow([
                            '\\N' if pd.isna(value) or value == '' else str(value) for value in row
                        ])
                    buffer.seek(0)
                    cursor.copy_expert(f"COPY {cls._meta.table_name} ({','.join(data.columns)}) FROM STDIN WITH CSV NULL AS '\\N'", buffer)
        else:
            data = data.to_dict(orient='records')
            with cls._meta.database.atomic():
                for batch in partition_all(batch_size, data):
                    cls.insert_many(batch).execute()
    
    @classmethod
    def reload(cls):
        cls.db_manager.reload()
        new_table = cls.db_manager.load_table_class(cls._meta.table_name)
        new_attrs = dir(new_table)
        attrs = dir(cls)
        for attr in attrs:
            if attr not in new_attrs:
                delattr(cls, attr)
        for attr in new_attrs:
            if not attr.startswith('__'):
                setattr(cls, attr, getattr(new_table, attr))



class Tables:
    def __init__(self, db):
        self.db = db
        self.tables = {}

    def __contains__(self, name):
        return name in self.db.meta

    def __getitem__(self, name):
        if name not in self.tables:
            if name in self.db.registered_models:
                self.tables[name] = self.db.registered_models[name]
            else:
                if name not in self.db.meta:
                    raise KeyError(f'Table {name} does not exist. Use db.create_table to create it.')
                self.tables[name] = self.db.load_table_class(name)
        return self.tables[name]
    
    def __getattr__(self, name):
        return self[name]
    
    def __repr__(self):
        return f"{self.db.meta.keys()}"


class Database:
    def __init__(self, connection=POSTGRES_URL, registered_models=[]):
        self.connection = connection
        self.db = None
        self.connect()
        self.registered_models = {}
        for model in registered_models:
            self.register_model(model)
        self.t = Tables(self)
        self.cache = {}
    
    def connect(self):
        url = urlparse(self.connection)
        self.db = PostgresqlExtDatabase(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )

    @property
    def meta(self):
        if 'meta' not in self.cache:
            meta = {}
            introspector = Introspector.from_database(self.db)
            metadata = introspector.introspect()
            fks = metadata.foreign_keys
            for table_name, columns in metadata.columns.items():
                meta[table_name] = {
                    'name': metadata.model_names[table_name],
                    'columns': columns,
                }
                if table_name in fks:
                    meta[table_name]['foreign_keys'] = {
                        x.column: x for x in fks[table_name]
                    }
            self.cache['meta'] = meta
        return self.cache['meta']
    
    def reload(self):
        self.close()
        self.__init__(
            connection=self.connection, 
            registered_models=list(self.registered_models.values())
        )

    def register_model(self, model):
        self.registered_models[model._meta.table_name] = model
        model.db_manager = self
        model._meta.database = self.db

    def load_table_class(self, name, new=False):
        if not new and name not in self.meta:
            raise KeyError(f'Table {name} does not exist. Use db.create_table to create it.')

        class Meta:
            database = self.db
            table_name = name
        
        attrs = {'Meta': Meta}

        if not new:
            table_meta = self.meta[name]
            for column_name, column in table_meta['columns'].items():
                keeps = ['column_name', 'index', 'primary_key', 'unique', 'default', 'model']
                rename = {'nullable': 'null'}
                column_args = {
                    k: v for k, v in column.__dict__.items() 
                    if k in keeps + list(rename.keys())
                }
                fk = table_meta['foreign_keys'].get(column_args['column_name'])
                if fk:
                    column_args['model'] = self.load_table_class(fk.dest_table)
                for k, v in rename.items():
                    column_args[v] = column_args.pop(k)
                attrs[column_name] = column.field_class(**column_args)
        TableClass = type(name, (CustomModel,), attrs)
        TableClass.db_manager = self
        return TableClass

    def create_table(self, name, exists_ok=True):
        if name in self.meta:
            if not exists_ok:
                raise ValueError(f'Table {name} already exists.')
            return
        table = self.load_table_class(name, new=True)
        self.db.create_tables([table])
        self.reload()

    @require_confirmation_wrapper(
        message=lambda args: notabs(f"""
            Are you sure you want to drop table '{args['name']}'?
            This will DELETE ALL TABLE DATA
        """),
        disable=lambda args: not args.get('confirm', True),
    )
    def drop_table(self, name, confirm=True):
        table = self.t[name]
        self.db.drop_tables([table])
        self.reload()

    def close(self):
        self.db.close()


def connect(connection=POSTGRES_URL):
    return Database(connection)
