# Services Quickstart

Docket Analyzer includes helpers for common infrastructure services.

## PostgreSQL

```python
from docketanalyzer import load_psql

db = load_psql()
status = db.status()
print("connected", status)
```

Use `db.t.TABLE` to access schemaless tables or register your own `DatabaseModel` classes.

## Redis

```python
from docketanalyzer import load_redis
redis = load_redis()
redis.ping()
```

## S3

```python
from docketanalyzer import load_s3
s3 = load_s3()

# Sync local data to the bucket
s3.push()
```
