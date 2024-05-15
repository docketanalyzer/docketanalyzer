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
]


config = EnvConfig(
    path=Path.home() / '.cache' / 'docketanalyzer' / 'config.json',
    config_keys=keys,
    cli_command='da configure',
)
