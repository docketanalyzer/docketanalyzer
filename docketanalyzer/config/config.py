from pathlib import Path
from docketanalyzer.config.env_config import EnvConfig, ConfigKey


keys = [
    ConfigKey(
        name='DA_DATA_DIR',
        key_type='path',
        description='\nChoose directory for data managed by Docket Analyzer\n',
        default=Path.home() / 'docketanalyzer',
        group='docketanalyzer',
    ),
    ConfigKey(
        name='COURTLISTENER_TOKEN',
        key_type='str',
        description='\nConfigure CourtListener API\n',
        default=None,
        mask=True,
        group='recap',
    ),
    ConfigKey(
        name='PACER_USERNAME',
        key_type='str',
        description='\nConfigure PACER Credentials\n',
        default=None,
        group='pacer',
    ),
    ConfigKey(
        name='PACER_PASSWORD',
        key_type='str',
        default=None,
        mask=True,
        group='pacer',
    ),
    ConfigKey(
        name='HF_TOKEN',
        key_type='str',
        description='\nConfigure Hugging Face Token\n',
        default=None,
        mask=True,
        group='huggingface',
    ),
    ConfigKey(
        name='GROQ_API_KEY',
        key_type='str',
        description='\nConfigure Groq\n',
        default=None,
        mask=True,
        group='groq',
    ),
    ConfigKey(
        name='GROQ_DEFAULT_CHAT_MODEL',
        key_type='str',
        default='Llama3-70b-8192',
        group='groq',
    ),
    ConfigKey(
        name='OPENAI_API_KEY',
        key_type='str',
        description='\nConfigure OpenAI\n',
        default=None,
        mask=True,
        group='openai',
    ),
    ConfigKey(
        name='OPENAI_ORG_ID',
        key_type='str',
        default=None,
        mask=True,
        group='openai',
    ),
    ConfigKey(
        name='OPENAI_DEFAULT_CHAT_MODEL',
        key_type='str',
        default='gpt-4o',
        group='openai',
    ),
    ConfigKey(
        name='OPENAI_DEFAULT_EMBEDDING_MODEL',
        key_type='str',
        default='text-embedding-3-large',
        group='openai',
    ),
    ConfigKey(
        name='POSTGRES_HOST',
        key_type='str',
        description='\nConfigure Postgres\n',
        default=None,
        group='postgres',
    ),
    ConfigKey(
        name='POSTGRES_PORT',
        key_type='int',
        default=5432,
        group='postgres',
    ),
    ConfigKey(
        name='POSTGRES_USERNAME',
        key_type='str',
        default='admin',
        group='postgres',
    ),
    ConfigKey(
        name='POSTGRES_PASSWORD',
        key_type='str',
        default=None,
        mask=True,
        group='postgres',
    ),
    ConfigKey(
        name='POSTGRES_DB',
        key_type='str',
        default='docketanalyzer',
        group='postgres',
    ),
    ConfigKey(
        name='ELASTIC_URL',
        key_type='str',
        description='\nConfigure Elasticsearch\n',
        default=None,
        group='elastic',
    ),
    ConfigKey(
        name='AWS_ACCESS_KEY_ID',
        key_type='str',
        description='\nConfigure AWS S3\n',
        default=None,
        mask=True,
        group='s3',
    ),
    ConfigKey(
        name='AWS_SECRET_ACCESS_KEY',
        key_type='str',
        default=None,
        mask=True,
        group='s3',
    ),
    ConfigKey(
        name='AWS_S3_BUCKET_NAME',
        key_type='str',
        default=None,
        group='s3',
    ),
    ConfigKey(
        name='AWS_S3_ENDPOINT_URL',
        key_type='str',
        default=None,
        group='s3',
    ),
    ConfigKey(
        name='AWS_S3_REGION_NAME',
        key_type='str',
        default=None,
        group='s3',
    ),
]


config = EnvConfig(
    path=Path.home() / '.cache' / 'docketanalyzer' / 'config.json',
    config_keys=keys,
    cli_command='da configure',
)
