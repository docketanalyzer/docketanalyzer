# PACER Quickstart

This page shows the minimal steps needed to download docket information and documents from PACER.

## Configure Credentials

Set your PACER username and password:

```bash
da configure pacer
```

## Fetch a Docket

```python
from docketanalyzer import Pacer, construct_docket_id

court = "insd"
docket_number = "1:24-cv-00524"
docket_id = construct_docket_id(court, docket_number)

pacer = Pacer()
docket_html, docket_json = pacer.purchase_docket(docket_id)
print(docket_json["case_name"])
```

## Download a Document

```python
entry = docket_json["entries"][0]

pdf, status = pacer.purchase_document(
    pacer_case_id=docket_json["pacer_case_id"],
    pacer_doc_id=entry["pacer_doc_id"],
    court=court,
)
```
