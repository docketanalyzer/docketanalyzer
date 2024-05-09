from pathlib import Path
from configuration_maker import Config, ConfigKey


keys = [
    ConfigKey(
        name='DA_DATA_DIR',
        key_type='path',
        description='Directory to store data managed by docketanalyzer',
        default=Path.home() / 'docketanalyzer',
    ),
    ConfigKey(
        name='COURTLISTENER_TOKEN',
        key_type='str',
        description='API token for CourtListener',
        default=None,
    ),
    ConfigKey(
        name='PACER_USERNAME',
        key_type='str',
        description='Username for PACER',
        default=None,
    ),
    ConfigKey(
        name='PACER_PASSWORD',
        key_type='str',
        description='Password for PACER',
        default=None,
    ),
    ConfigKey(
        name='POSTGRES_HOST',
        key_type='str',
        description='Postgres host',
        default=None,
    ),
    ConfigKey(
        name='POSTGRES_PORT',
        key_type='int',
        description='Postgres port',
        default=5432,
    ),
    ConfigKey(
        name='POSTGRES_USERNAME',
        key_type='str',
        description='Postgres username',
        default=None,
    ),
    ConfigKey(
        name='POSTGRES_PASSWORD',
        key_type='str',
        description='Postgres password',
        default=None,
    ),
    ConfigKey(
        name='POSTGRES_DB',
        key_type='str',
        description='Postgres database',
        default='docketanalyzer',
    ),
]


config = Config(
    path=Path.home() / '.cache' / 'docketanalyzer' / 'config.json',
    config_keys=keys,
    cli_command='da configure',
)
