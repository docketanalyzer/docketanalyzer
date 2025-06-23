import csv
from collections.abc import Generator
from io import StringIO
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import peewee
from peewee import Field, Model, ModelSelect
from playhouse.migrate import PostgresqlMigrator, migrate
from playhouse.postgres_ext import PostgresqlExtDatabase
from playhouse.reflection import Introspector
from playhouse.shortcuts import model_to_dict
from tqdm import tqdm

from .. import env, notabs


class CustomQueryMixin:
    """Custom query mixin for Peewee models."""

    def pandas(self, *columns: str, copy: bool = False) -> pd.DataFrame:
        """Convert query results directly to a pandas DataFrame.

        This method allows for selecting specific columns and optionally using
        the Postgres COPY command for faster data retrieval.

        Args:
            *columns: Specific columns to include in the DataFrame
            copy (bool): Whether to use Postgres COPY command
        """
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
                ).decode("utf-8")
                buffer = StringIO()
                cursor.copy_expert(copy_sql, buffer)
                buffer.seek(0)
                data = pd.read_csv(buffer)
        else:
            data = pd.DataFrame(list(query.dicts()))

        return data

    def sample(self, n: int) -> "DatabaseModelSelect":
        """Randomly sample n records from the query.

        This method orders the query by a random function and limits the results to n.

        Args:
            n (int): Number of records to sample
        Returns:
            DatabaseModelSelect: Query object for the random sample
        """
        return self.order_by(peewee.fn.Random()).limit(n)

    def batch(
        self, n: int, verbose: bool = True
    ) -> Generator["DatabaseModelSelect", None, None]:
        """Iterate over query results in batches of size n.

        Args:
            n (int): Batch size
            verbose (bool): Whether to show progress bar
        Yields:
            DatabaseModelSelect: Query object for each batch
        """
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
    """ModelSelect with custom query mixin."""

    pass


class DatabaseModelQueryMixin:
    """Custom query mixin for Peewee models.

    This mixin adds DataFrame conversion, batch processing, and sampling functionality
    to Peewee queries.
    """

    @classmethod
    def select(cls, *fields: Field) -> DatabaseModelSelect:
        """Select fields from the model for the query.

        Preselects all fields if no select has been applied.

        Args:
            *fields: Specific fields to include in the query
        Returns:
            DatabaseModelSelect: Query object for the selected fields
        """
        is_default = not fields
        if not fields:
            fields = cls._meta.sorted_fields
        return DatabaseModelSelect(cls, fields, is_default=is_default)

    @classmethod
    def sample(cls, n: int) -> DatabaseModelSelect:
        """Randomly sample n records from the query.

        Args:
            n (int): Number of records to sample

        Returns:
            DatabaseModelSelect: Query object for the random sample
        """
        return cls.select(cls).sample(n)

    @classmethod
    def pandas(cls, *columns: str, copy: bool = False) -> pd.DataFrame:
        """Convert query results directly to a pandas DataFrame.

        Args:
            *columns: Specific columns to include in the DataFrame
            copy (bool): Whether to use Postgres COPY command
                (better for large batch sizes)

        Returns:
            pd.DataFrame: Query results as a DataFrame
        """
        return cls.select(cls).pandas(*columns, copy=copy)

    @classmethod
    def where(cls, *args: Any, **kwargs: Any) -> DatabaseModelSelect:
        """Filter the query results based on conditions.

        Preselects all fields if no select has been applied.

        Args:
            *args: Conditions to filter the query
            **kwargs: Additional keyword arguments for filtering
        Returns:
            DatabaseModelSelect: Query object for the filtered results
        """
        return cls.select(cls).where(*args, **kwargs)

    @classmethod
    def batch(
        cls, n: int, verbose: bool = False
    ) -> Generator[DatabaseModelSelect, None, None]:
        """Iterate over query results in batches of size n.

        Args:
            n (int): Batch size
            verbose (bool): Whether to show progress bar

        Yields:
            DatabaseModelSelect: Query object for each batch
        """
        return cls.select(cls).batch(n, verbose=verbose)

    @classmethod
    def count(cls) -> int:
        """Count the number of records in the query.

        Returns:
            int: Number of records matching the query
        """
        return cls.select().count()

    def dict(self) -> dict[str, Any]:
        """Convert the current model instance to a dictionary.

        Returns:
            dict: Dictionary representation of the model instance
        """
        return model_to_dict(self)


class DatabaseModel(DatabaseModelQueryMixin, Model):
    """A base model class that extends Peewee's Model with additional functionality.

    This class provides enhanced database operations including pandas DataFrame
        conversion, batch processing, column management, and model reloading
        capabilities.
    """

    db_manager = None

    @classmethod
    def drop_column(cls, column_name: str, confirm: bool = True) -> None:
        """Drop a column from the database table.

        Args:
            column_name (str): Name of the column to drop
            confirm (bool): Whether to prompt for confirmation before dropping
        """
        table_name = cls._meta.table_name
        if confirm:
            response = input(
                notabs(f"""
                Are you sure you want to drop '{column_name}' from '{table_name}'?
                This will DELETE ALL COLUMN DATA.

                Are you sure you want to proceed? (y/n):
            """)
            ).lower()
            if response != "y":
                raise Exception("Aborted")
        migrator = PostgresqlMigrator(cls._meta.database)
        migrate(migrator.drop_column(table_name, column_name))
        cls.reload()

    @classmethod
    def add_column(
        cls,
        column_name: str,
        column_type: str,
        null: bool = True,
        overwrite: bool = False,
        exists_ok: bool = True,
        **kwargs: Any,
    ) -> None:
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
        if column_name in table_meta["columns"]:
            if not exists_ok:
                raise ValueError(
                    f"Column {column_name} already exists in table {table_name}."
                )
            if not overwrite:
                return
            cls.drop_column(column_name)

        kwargs["null"] = null
        migrate(
            migrator.add_column(
                table_name, column_name, getattr(peewee, column_type)(**kwargs)
            )
        )
        cls.reload()

    @classmethod
    def add_data(
        cls, data: pd.DataFrame, copy: bool = False, batch_size: int = 1000
    ) -> None:
        """Add data to the table from a pandas DataFrame.

        Args:
            data (pd.DataFrame): DataFrame containing the data to insert
            copy (bool): Whether to use Postgres COPY command for faster insertion
            batch_size (int): Number of records to insert in each batch
                when not using COPY
        """
        if copy:
            conn = cls._meta.database.connection()
            with conn.cursor() as cursor:
                buffer = StringIO()
                csv_writer = csv.writer(
                    buffer, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
                )
                for _, row in data.iterrows():
                    csv_writer.writerow(
                        [
                            "\\N" if pd.isna(value) or value == "" else str(value)
                            for value in row
                        ]
                    )
                buffer.seek(0)

                cols = ",".join(data.columns)
                table_name = cls._meta.table_name
                cursor.copy_expert(
                    f"COPY {table_name} ({cols}) FROM STDIN WITH CSV NULL AS '\\N'",
                    buffer,
                )
        else:
            data = data.to_dict(orient="records")
            with cls._meta.database.atomic():
                for i in range(0, len(data), batch_size):
                    batch = data[i : i + batch_size]
                    cls.insert_many(batch).execute()

    @classmethod
    def reload(cls):
        """Reload the model class to reflect any changes in the database schema."""
        cls.db_manager.reload()
        new_table = cls.db_manager.load_table_class(cls._meta.table_name)
        new_attrs = dir(new_table)
        attrs = dir(cls)
        for attr in attrs:
            if attr not in new_attrs:
                delattr(cls, attr)
        for attr in new_attrs:
            if not attr.startswith("__"):
                setattr(cls, attr, getattr(new_table, attr))


class Tables:
    """A class to manage database tables and provide access to their models."""

    def __init__(self, db: "Database") -> None:
        """Initialize the Tables object with a database connection.

        Args:
            db (Database): Database connection object
        """
        self.db = db
        self.tables: dict[str, type[DatabaseModel]] = {}

    def __contains__(self, name: str) -> bool:
        """Check if the table exists in the database.

        Args:
            name (str): Name of the table to check
        Returns:
            bool: True if the table exists, False otherwise
        """
        return name in self.db.meta

    def __getitem__(self, name: str) -> type[DatabaseModel]:
        """Return the table class for the given name.

        Args:
            name (str): Name of the table to retrieve
        Returns:
            type: The table class corresponding to the name
        Raises:
            KeyError: If the table does not exist in the database
        """
        if name not in self.tables:
            if name in self.db.registered_models:
                self.tables[name] = self.db.registered_models[name]
            else:
                if name not in ["dockets_index"]:
                    print(
                        f"Warning: Inferring table schema for table {name}. "
                        "This is slow! Better to explicitly register the table."
                    )
                if name not in self.db.meta:
                    raise KeyError(
                        f"Table {name} does not exist. "
                        "Use db.create_table to create it."
                    )
                self.tables[name] = self.db.load_table_class(name)
        return self.tables[name]

    def __getattr__(self, name: str) -> type[DatabaseModel]:
        """Return the table class for the given name.

        Args:
            name (str): Name of the table to retrieve
        Returns:
            type: The table class corresponding to the name
        """
        return self[name]

    def __repr__(self) -> str:
        """Return a string representation of the Tables object."""
        return f"{self.db.meta.keys()}"


class Database:
    """A PostgreSQL database manager that provides high-level database operations.

    This class handles database connections, table management, model registration,
        and provides an interface for table operations with schemaless tables through
        the Tables class.
    """

    def __init__(
        self,
        connection: str | None = None,
        registered_models: list[type[DatabaseModel]] | None = None,
    ) -> None:
        """Initialize the database manager.

        Args:
            connection (str, optional): PostgreSQL connection URL
            registered_models (list): List of model classes to register with
                the database
        """
        self.connection = connection or env.POSTGRES_URL
        self.db: PostgresqlExtDatabase | None = None
        self.connect()
        self.registered_models: dict[str, type[DatabaseModel]] = {}
        if registered_models is not None:
            for model in registered_models:
                self.register_model(model)
        self.t = Tables(self)
        self.cache: dict[str, Any] = {}

    def connect(self) -> None:
        """Establish connection to the PostgreSQL database using the connection URL."""
        url = urlparse(self.connection)
        self.db = PostgresqlExtDatabase(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
        )

    def status(self) -> bool:
        """Check if the database connection is working.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        return self.db.connect()

    @property
    def meta(self) -> dict[str, dict[str, Any]]:
        """Get database metadata including table and column information.

        Returns:
            dict: Database metadata including table schemas and foreign keys
        """
        if "meta" not in self.cache:
            meta = {}
            introspector = Introspector.from_database(self.db)
            metadata = introspector.introspect()
            fks = metadata.foreign_keys
            for table_name, columns in metadata.columns.items():
                meta[table_name] = {
                    "name": metadata.model_names[table_name],
                    "columns": columns,
                }
                if table_name in fks:
                    meta[table_name]["foreign_keys"] = {
                        x.column: x for x in fks[table_name]
                    }
            self.cache["meta"] = meta
        return self.cache["meta"]

    def reload(self):
        """Reload the database metadata and registered models."""
        self.close()
        self.__init__(
            connection=self.connection,
            registered_models=list(self.registered_models.values()),
        )

    def register_model(self, model: type[DatabaseModel]) -> None:
        """Register a model class with the database manager.

        Args:
            model: Peewee model class to register
        """
        self.registered_models[model._meta.table_name] = model
        model.db_manager = self
        model._meta.database = self.db

    def load_table_class(self, name: str, new: bool = False) -> type[DatabaseModel]:
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
            raise KeyError(
                f"Table {name} does not exist. Use db.create_table to create it."
            )

        class Meta:
            database = self.db
            table_name = name

        attrs = {"Meta": Meta}

        if not new:
            table_meta = self.meta[name]
            for column_name, column in table_meta["columns"].items():
                keeps = [
                    "column_name",
                    "index",
                    "primary_key",
                    "unique",
                    "default",
                    "model",
                ]
                rename = {"nullable": "null"}
                column_args = {
                    k: v
                    for k, v in column.__dict__.items()
                    if k in keeps + list(rename.keys())
                }
                fk = table_meta["foreign_keys"].get(column_args["column_name"])
                if fk:
                    column_args["model"] = self.load_table_class(fk.dest_table)
                for k, v in rename.items():
                    column_args[v] = column_args.pop(k)
                attrs[column_name] = column.field_class(**column_args)
        table_class = type(name, (DatabaseModel,), attrs)
        table_class.db_manager = self
        return table_class

    def create_table(
        self, name_or_model: str | type[DatabaseModel], exists_ok: bool = True
    ) -> None:
        """Create a new table in the database.

        Args:
            name_or_model (Union[str, Type[DatabaseModel]]): Name of the table to
                create or model class
            exists_ok (bool): Whether to silently continue if table exists

        Raises:
            ValueError: If table exists and exists_ok=False
        """
        if isinstance(name_or_model, str):
            name = name_or_model
            if name in self.meta:
                if not exists_ok:
                    raise ValueError(f"Table {name} already exists.")
                return
            table = self.load_table_class(name, new=True)
        else:
            table = name_or_model
        self.db.create_tables([table])
        self.reload()

    def drop_table(self, name: str, confirm: bool = True):
        """Drop a table from the database.

        Args:
            name (str): Name of the table to drop
            confirm (bool): Whether to prompt for confirmation before dropping

        Raises:
            Exception: If confirmation is required and user does not confirm
        """
        if confirm:
            response = input(
                notabs(f"""
                Are you sure you want to drop table '{name}'?
                This will DELETE ALL TABLE DATA.

                Are you sure you want to proceed? (y/n):
            """)
            ).lower()
            if response != "y":
                raise Exception("Aborted")
        table = self.t[name]
        self.db.drop_tables([table])
        self.reload()

    def close(self) -> None:
        """Close the database connection."""
        self.db.close()


def load_psql() -> Database:
    """Load a Database object using the connection url in your config.

    Run `da configure postgres` to set your PostgreSQL connection URL.
    """
    return Database(env.POSTGRES_URL)
