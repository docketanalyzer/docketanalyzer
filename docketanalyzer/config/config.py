from pathlib import Path
from docketanalyzer.config.env_config import EnvConfig, ConfigKey


keys = [
    ConfigKey(
        name='DA_DATA_DIR',
        key_type='path',
        description='\nChoose directory for data managed by Docket Analyzer\n',
        default=Path.home() / 'docketanalyzer',
    ),
    ConfigKey(
        name='COURTLISTENER_TOKEN',
        key_type='str',
        description='\nConfigure CourtListener API\n',
        default=None,
        mask=True,
    ),
    ConfigKey(
        name='PACER_USERNAME',
        key_type='str',
        description='\nConfigure PACER Credentials\n',
        default=None,
    ),
    ConfigKey(
        name='PACER_PASSWORD',
        key_type='str',
        default=None,
        mask=True,
    ),
    ConfigKey(
        name='POSTGRES_HOST',
        key_type='str',
        description='\nConfigure Postgres\n',
        default=None,
    ),
    ConfigKey(
        name='POSTGRES_PORT',
        key_type='int',
        default=5432,
    ),
    ConfigKey(
        name='POSTGRES_USERNAME',
        key_type='str',
        default='admin',
    ),
    ConfigKey(
        name='POSTGRES_PASSWORD',
        key_type='str',
        default=None,
        mask=True,
    ),
    ConfigKey(
        name='POSTGRES_DB',
        key_type='str',
        default='docketanalyzer',
    ),
    ConfigKey(
        name='ELASTIC_HOST',
        key_type='str',
        description='\nConfigure Elasticsearch\n',
        default=None,
    ),
    ConfigKey(
        name='ELASTIC_PORT',
        key_type='int',
        default=9200,
    ),
    ConfigKey(
        name='ELASTIC_USERNAME',
        key_type='str',
        default=None,
    ),
    ConfigKey(
        name='ELASTIC_PASSWORD',
        key_type='str',
        default=None,
        mask=True,
    ),
    ConfigKey(
        name='AWS_ACCESS_KEY_ID',
        key_type='str',
        description='\nConfigure AWS S3\n',
        default=None,
        mask=True,
    ),
    ConfigKey(
        name='AWS_SECRET_ACCESS_KEY',
        key_type='str',
        default=None,
        mask=True,
    ),
    ConfigKey(
        name='AWS_S3_BUCKET_NAME',
        key_type='str',
        default=None,
    ),
    ConfigKey(
        name='AWS_S3_ENDPOINT_URL',
        key_type='str',
        default=None,
    ),
    ConfigKey(
        name='AWS_S3_REGION_NAME',
        key_type='str',
        default=None,
    ),
]


config = EnvConfig(
    path=Path.home() / '.cache' / 'docketanalyzer' / 'config.json',
    config_keys=keys,
    cli_command='da configure',
)
