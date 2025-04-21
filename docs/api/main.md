# docketanalyzer

## Docket Management

::: docketanalyzer.Pacer
    options:
      heading_level: 3
      members:
        - purchase_docket
        - purchase_document
        - purchase_attachment
        - parse
        - find_candidate_cases


## Services

::: docketanalyzer.services
    options:
      heading_level: 2
      members_order: source

::: docketanalyzer.load_psql
    options:
      heading_level: 3

::: docketanalyzer.load_redis
    options:
      heading_level: 3

::: docketanalyzer.load_s3
    options:
      heading_level: 3

::: docketanalyzer.Database
    options:
      heading_level: 3
      members:
        - __init__
        - connect
        - create_table
        - register_model

::: docketanalyzer.DatabaseModel
    options:
      heading_level: 3

::: docketanalyzer.S3
    options:
      heading_level: 3
      members:
        - __init__
        - push
        - pull
        - upload
        - download
        - delete
        - status

::: docketanalyzer.utils
    options:
      heading_level: 2
      members_order: source


::: docketanalyzer.Registry
    options:
      heading_level: 3
