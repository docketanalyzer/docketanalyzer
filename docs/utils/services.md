# Services

## Postgres

Docket Analyzer includes a custom PostgreSQL wrapper built on top of the
[Peewee ORM](https://docs.peewee-orm.com/). The wrapper is designed to make it
easy to work with existing tables or create "schemaless" tables on the fly.
It also extends Peewee's query API with convenience methods for pandas support
and batch operations.

### Connecting

```python
from docketanalyzer import load_psql

db = load_psql()
```

`load_psql()` reads the connection URL from `da configure postgres` and returns a
`Database` instance. The object lazily introspects your database to discover
available tables.

### Schemaless tables

You may create an empty table by name and then add columns dynamically. Tables
loaded this way infer their schema via introspection each time they are
accessed, so registering a model is recommended for performance.

```python
# Create an empty table and add columns
from peewee import TextField, IntegerField
import pandas as pd

# create the table if it doesn't exist
db.create_table("users")

# access via db.t.<table_name>
users = db.t.users

users.add_column("email", column_type="TextField", unique=True)
users.add_column("age", column_type="IntegerField")

# insert data from a DataFrame
users.add_data(pd.DataFrame([
    {"email": "alice@example.com", "age": 30},
    {"email": "bob@example.com", "age": 25},
]))
```

### Registering models

For better performance and type checking you can register a standard Peewee
model with the database. Registered models bypass introspection and provide the
same extended query API.

```python
class User(DatabaseModel):
    email = TextField(unique=True)
    age = IntegerField()

    class Meta:
        table_name = "users"

# register and create the table
db.register_model(User)
db.create_table(User)

# queries now use the registered model
users = db.t.users
```

### Extended query API

The table classes returned by `db.t` inherit several helpers in addition to the
standard Peewee interface:

- `select()` automatically selects all columns if none are specified.
- `where()` uses the extended select and returns a query object that supports
  pandas conversion.
- `pandas(*cols, copy=False)` converts query results directly to a
  `pandas.DataFrame`. Setting `copy=True` uses the PostgreSQL `COPY` command for
  large transfers.
- `sample(n)` returns a randomly sampled query.
- `batch(n, verbose=True)` yields query results in chunks of `n` rows.
- Instances provide `dict()` for easy serialization.

Example usage:

```python
# get all rows as a DataFrame
all_rows = users.pandas(copy=True)

# filter and select specific columns
emails = users.where(users.age > 20).pandas("email")

# sample and batch processing
for batch in users.sample(100).batch(25, verbose=False):
    process(batch.pandas())

# delete by condition
users.delete().where(users.email == "bob@example.com").execute()
```

### Modifying tables

Tables support schema modifications without manually writing migrations:

- `add_column(name, column_type, **kwargs)` – add a new column using Peewee
  field type names.
- `drop_column(name)` – remove a column (prompts for confirmation by default).
- `reload()` – reload the model definition from the database after structural
  changes.
- `add_data(df, copy=False, batch_size=1000)` – insert DataFrame rows using the
  high‑level helpers.

```python
# add a new column and reload the model
users.add_column("created", column_type="DateTimeField")
users.reload()
```
