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

::: docketanalyzer_core.services
    options:
      heading_level: 2
      members_order: source

::: docketanalyzer_core.load_psql
    options:
      heading_level: 3

::: docketanalyzer_core.load_redis
    options:
      heading_level: 3

::: docketanalyzer_core.load_s3
    options:
      heading_level: 3

::: docketanalyzer_core.Database
    options:
      heading_level: 3
      members:
        - __init__
        - connect
        - create_table
        - register_model

::: docketanalyzer_core.DatabaseModel
    options:
      heading_level: 3

::: docketanalyzer_core.S3
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

::: docketanalyzer_core.utils
    options:
      heading_level: 2
      members_order: source


::: docketanalyzer_core.Registry
    options:
      heading_level: 3
