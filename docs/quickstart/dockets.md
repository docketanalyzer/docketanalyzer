# Docket Management Quickstart

The `DocketIndex` organizes docket data on disk and in your database.

## Load the Index

```python
from docketanalyzer import load_docket_index

index = load_docket_index()
```

By default the index stores data under `DA_DATA_DIR/data/dockets`. Use `da configure docketanalyzer` to change `DA_DATA_DIR`.

## Add Local Docket IDs

If you already have docket folders on disk, add them to the index:

```python
index.add_local_docket_ids()
```

## Access an Individual Docket

```python
manager = index["insd__1_24-cv-00524"]
print(manager.docket_json["case_name"])
```

The manager exposes helpers for locating document PDFs and OCR files and can `push` or `pull` data to S3 via the index's S3 service.
