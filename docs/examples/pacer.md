# Download PACER Data

The `PACER` class provides a simplified interface for downloading dockets and documents from PACER with [juriscraper](https://github.com/freelawproject/juriscraper).

You can set your PACER credentials by running:
```bash
da configure pacer
```

## Purchase and parse a docket

```python
from docketanalyzer import PACER, construct_docket_id

court, docket_number = "insd", "1:24-cv-00524"
docket_id = construct_docket_id(court, docket_number) # "insd__1_24-cv-00524"

pacer = PACER()
docket_html, docket_json = pacer.purchase_docket(docket_id)
print(json.dumps(docket_json, indent=2))
```

## Parse an existing HTML docket

```python
docket_json = pacer.parse(docket_html, court)
print(json.dumps(docket_json, indent=2))
```

## Download a document for a docket entry

```python
pacer_case_id = docket_json['pacer_case_id']
entry = docket_json['entries'][0] # First entry

pdf, status = pacer.purchase_document(
    pacer_case_id=pacer_case_id,
    pacer_doc_id=entry['pacer_doc_id'],
    court=court
)

if status == 'success':
    with open('document.pdf', 'wb') as f:
        f.write(pdf)
```

## Download an attachment

```python
pdf, status = pacer.purchase_attachment(
    pacer_case_id=pacer_case_id,
    pacer_doc_id=entry['pacer_doc_id'],
    attachment_number=1,  # First attachment
    court=court
)

if status == 'success':
    with open('attachment.pdf', 'wb') as f:
        f.write(pdf)
```
