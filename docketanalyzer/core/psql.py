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
from docketanalyzer import env, notabs


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


class DatabaseModelSelect(ModelSelect, CustomQueryMixin):
    pass


class DatabaseModelQueryMixin:
    """This mixin adds DataFrame conversion, batch processing, and sampling functionality
    to Peewee queries.
    """

    @classmethod
    def select(cls, *fields):
        is_default = not fields
        if not fields:
            fields = cls._meta.sorted_fields
        return DatabaseModelSelect(cls, fields, is_default=is_default)

    @classmethod
    def sample(cls, n):
        """Randomly sample n records from the query.

        Args:
            n (int): Number of records to sample

        Returns:
            DatabaseModelSelect: Query object for the random sample
        """
        return cls.select(cls).sample(n)
    
    @classmethod
    def pandas(cls, *columns, copy=False):
        """Convert query results directly to a pandas DataFrame.

        Args:
            *columns: Specific columns to include in the DataFrame
            copy (bool): Whether to use Postgres COPY command (better for large batch sizes)

        Returns:
            pd.DataFrame: Query results as a DataFrame
        """
        return cls.select(cls).pandas(*columns, copy=copy)

    @classmethod
    def where(cls, *args, **kwargs):
        return cls.select(cls).where(*args, **kwargs)

    @classmethod
    def batch(cls, n, verbose=False):
        """Iterate over query results in batches of size n.

        Args:
            n (int): Batch size
            verbose (bool): Whether to show progress bar

        Yields:
            DatabaseModelSelect: Query object for each batch
        """
        return cls.select(cls).batch(n, verbose=verbose)
    
    @classmethod
    def count(cls):
        return cls.select().count()

    def dict(self):
        return model_to_dict(self)


class DatabaseModel(DatabaseModelQueryMixin, Model):
    """A base model class that extends Peewee's Model with additional database functionality.
    
    This class provides enhanced database operations including pandas DataFrame conversion,
    batch processing, column management, and model reloading capabilities.
    """
    db_manager = None

    @classmethod
    def drop_column(cls, column_name, confirm=True):
        """Drop a column from the database table.
        
        Args:
            column_name (str): Name of the column to drop
            confirm (bool): Whether to prompt for confirmation before dropping
        """
        if confirm:
            response = input(notabs(f"""
                Are you sure you want to drop column '{column_name}' from '{cls._meta.table_name}'?
                This will DELETE ALL COLUMN DATA.

                Are you sure you want to proceed? (y/n):
            """)).lower()
            if response != 'y':
                raise Exception("Aborted")
        table_name = cls._meta.table_name
        migrator = PostgresqlMigrator(cls._meta.database)
        migrate(migrator.drop_column(table_name, column_name))
        cls.reload()

    @classmethod
    def add_column(cls, column_name, column_type, null=True, overwrite=False, exists_ok=True, **kwargs):
        """Add a new column to the database table.
        
        Args:
            column_name (str): Name of the new column
            column_type (str): Peewee field type for the column
            null (bool, optional): Whether the column can contain NULL values
            overwrite (bool): Whether to overwrite if column exists
            exists_ok (bool): Whether to silently continue if column exists
            **kwargs: Additional field parameters passed to Peewee
        """
        table_name = cls._meta.table_name
        table_meta = cls.db_manager.meta[table_name]
        migrator = PostgresqlMigrator(cls._meta.database)
        if column_name in table_meta['columns']:
            if not exists_ok:
                raise ValueError(f'Column {column_name} already exists in table {table_name}.')
            if not overwrite:
                return
            cls.drop_column(column_name)

        kwargs['null'] = null
        migrate(
            migrator.add_column(table_name, column_name, getattr(peewee, column_type)(**kwargs))
        )
        cls.reload()
    
    @classmethod
    def add_data(cls, data, copy=False, batch_size=1000):
        """Add data to the table from a pandas DataFrame.
        
        Args:
            data (pd.DataFrame): DataFrame containing the data to insert
            copy (bool): Whether to use Postgres COPY command for faster insertion
            batch_size (int): Number of records to insert in each batch when not using COPY
        """
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
                if name not in ['dockets_index']:
                    print(f"Warning: Inferring table schema for table {name}. This is slow! Better to explicitly register the table.")
                if name not in self.db.meta:
                    raise KeyError(f'Table {name} does not exist. Use db.create_table to create it.')
                self.tables[name] = self.db.load_table_class(name)
        return self.tables[name]
    
    def __getattr__(self, name):
        return self[name]
    
    def __repr__(self):
        return f"{self.db.meta.keys()}"


class Database:
    """A PostgreSQL database manager that provides high-level database operations.
    
    This class handles database connections, table management, model registration,
    and provides an interface for table operations with schemaless tables through the Tables class.

    Examples
    --------
    Connect to database and create a table:

    .. code-block:: python

        db = Database()
        
        # Access table through the Tables interface
        Users = db.t.users
        
    Define and register a custom model:

    .. code-block:: python
        import peewee as pw
        from docketanalyzer import Database, DatabaseModel

        class Test(DatabaseModel):
            email = pw.CharField(unique=True)
            name = pw.CharField()
            age = pw.IntegerField()
            registration_date = pw.DateTimeField()
            
            class Meta:
                table_name = 'test'
        
        db = Database()
        db.create_table(Test)
        
    Register a model to access it through the table interface:

    .. code-block:: python

        db.register_model(Test)
        table = db.t.test # table == Test

    Push data directly from DataFrames and convert query results back to pandas:

    .. code-block:: python
        data = pd.DataFrame({
            'email': ['alice@example.com', 'bob@example.com'],
            'name': ['Alice', 'Bob'],
            'age': [30, 25],
            'registration_date': [datetime(2020, 1, 1), datetime(2021, 1, 15)],
        })

        table.add_data(data)
        results = table.where(table.age > 25).pandas()

        assert len(results) == 1
        assert results.columns.tolist() == ['id', 'email', 'name', 'age', 'registration_date']
    
    Query data with enhanced features:

    .. code-block:: python
    
        for batch in Test.batch(1000):
            process_batch(batch)

        random_records = Test.sample(10)
    
    Create schemaless tables and infer table objects without a schema. 
    These are slow but useful for quickly accessing existing tables if the schema is unknown:

    .. code-block:: python

        db.create_table('schemaless_test')
        table = db.t.schemaless_test

        table.add_column('email', 'CharField', unique=True)
        table.add_column('name', 'CharField')
        table.add_column('age', 'IntegerField')
        table.add_column('registration_date', 'DateTimeField')

        table = db.t.schemaless_test # need to reload table after adding columns
        table.add_data(data)

        results = table.pandas()

        assert results['age'].dtype == 'int64'
        assert results['registration_date'].dtype == 'datetime64[ns]'
    """
    def __init__(self, connection=None, registered_models=[]):
        """Initialize the database manager.
        
        Args:
            connection (str, optional): PostgreSQL connection URL
            registered_models (list): List of model classes to register with the database
        """
        self.connection = connection or env.POSTGRES_URL
        self.db = None
        self.connect()
        self.registered_models = {}
        for model in registered_models:
            self.register_model(model)
        self.t = Tables(self)
        self.cache = {}
    
    def connect(self):
        """Establish connection to the PostgreSQL database using the connection URL."""
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
        """Get database metadata including table and column information.
        
        Returns:
            dict: Database metadata including table schemas and foreign key relationships
        """
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
        """Register a model class with the database manager.
        
        Args:
            model: Peewee model class to register
        """
        self.registered_models[model._meta.table_name] = model
        model.db_manager = self
        model._meta.database = self.db

    def load_table_class(self, name, new=False):
        """Dynamically create a model class for a database table.
        
        Args:
            name (str): Name of the table
            new (bool): Whether this is a new table being created
            
        Returns:
            type: A new DatabaseModel subclass representing the table
            
        Raises:
            KeyError: If table doesn't exist and new=False
        """
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
        TableClass = type(name, (DatabaseModel,), attrs)
        TableClass.db_manager = self
        return TableClass

    def create_table(self, name_or_model, exists_ok=True):
        """Create a new table in the database.
        
        Args:
            name (str): Name of the table to create
            exists_ok (bool): Whether to silently continue if table exists
            
        Raises:
            ValueError: If table exists and exists_ok=False
        """
        if isinstance(name_or_model, str):
            name = name_or_model
            if name in self.meta:
                if not exists_ok:
                    raise ValueError(f'Table {name} already exists.')
                return
            table = self.load_table_class(name, new=True)
        else:
            table = name_or_model
        self.db.create_tables([table])
        self.reload()

    def drop_table(self, name, confirm=True):
        if confirm:
            response = input(notabs(f"""
                Are you sure you want to drop table '{name}'?
                This will DELETE ALL TABLE DATA.

                Are you sure you want to proceed? (y/n):
            """)).lower()
            if response != 'y':
                raise Exception("Aborted")
        table = self.t[name]
        self.db.drop_tables([table])
        self.reload()

    def close(self):
        self.db.close()


def load_psql(connection=None):
    """Load a Database object using the connection url in your config.

    Run `da configure postgres` to set your PostgreSQL connection URL.
    """
    connection = connection or env.POSTGRES_URL
    return Database(connection)
