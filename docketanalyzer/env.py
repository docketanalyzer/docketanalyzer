import os
from pathlib import Path
from docketanalyzer.utils.config import Config, ConfigKey


env = Config(
    path=Path.home() / '.cache' / 'docketanalyzer' / 'config.json',
    keys=[
        ConfigKey(
            name='DA_DATA_DIR',
            alias_names=['DATA_DIR'],
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
            name='ANTHROPIC_API_KEY',
            key_type='str',
            description='\nConfigure Anthropic\n',
            default=None,
            mask=True,
            group='anthropic',
        ),
        ConfigKey(
            name='ANTHROPIC_DEFAULT_CHAT_MODEL',
            key_type='str',
            default='claude-3-5-sonnet-latest',
            group='anthropic',
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
            name='OPENAI_DEFAULT_CHAT_MODEL',
            key_type='str',
            default='gpt-4o-mini',
            group='openai',
        ),
        ConfigKey(
            name='OPENAI_DEFAULT_EMBEDDING_MODEL',
            key_type='str',
            default='text-embedding-3-large',
            group='openai',
        ),
        ConfigKey(
            name='COHERE_API_KEY',
            key_type='str',
            description='\nConfigure Cohere\n',
            default=None,
            mask=True,
            group='cohere',
        ),
        ConfigKey(
            name='COHERE_DEFAULT_CHAT_MODEL',
            key_type='str',
            default='command-r-plus',
            group='cohere',
        ),
        ConfigKey(
            name='TOGETHER_API_KEY',
            key_type='str',
            description='\nConfigure Together AI\n',
            default=None,
            mask=True,
            group='together',
        ),
        ConfigKey(
            name='TOGETHER_DEFAULT_CHAT_MODEL',
            key_type='str',
            default='meta-llama/Llama-3-70b-chat-hf',
            group='together',
        ),
        ConfigKey(
            name='RUNPOD_API_KEY',
            key_type='str',
            description='\nConfigure Runpod\n',
            default=None,
            mask=True,
            group='runpod',
        ),
        ConfigKey(
            name='REMOTE_INFERENCE_ENDPOINT_ID',
            key_type='str',
            default=None,
            mask=True,
            group='runpod',
        ),
        ConfigKey(
            name='REMOTE_ROUTINES_ENDPOINT_ID',
            key_type='str',
            default=None,
            mask=True,
            group='runpod',
        ),
        ConfigKey(
            name='WANDB_API_KEY',
            key_type='str',
            description='\nConfigure Weights and Biases\n',
            default=None,
            mask=True,
            group='wandb',
        ),
        ConfigKey(
            name='POSTGRES_URL',
            key_type='str',
            description='\nConfigure Postgres\n',
            default=None,
            mask=True,
            group='postgres',
        ),
        ConfigKey(
            name='ELASTIC_URL',
            key_type='str',
            description='\nConfigure Elasticsearch\n',
            default=None,
            mask=True,
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
            name='SELENIUM_HOST',
            key_type='str',
            description='\nConfigure Selenium\n',
            default='http://localhost',
            group='selenium',
        ),
        ConfigKey(
            name='SELENIUM_PORT',
            key_type='int',
            default=4444,
            group='selenium',
        ),
        ConfigKey(
            name='WEB_SEARCH_PORT',
            key_type='int',
            default=8080,
            group='websearch',
        ),
        ConfigKey(
            name='BASE_URL',
            key_type='str',
            description='\nConfigure Dev\n',
            default='http://localhost:5001',
            group='dev',
        ),
        ConfigKey(
            name='APP_HOST',
            key_type='str',
            default='127.0.0.1',
            group='dev',
        ),
        ConfigKey(
            name='APP_PORT',
            key_type='int',
            default=5002,
            group='dev',
        ),
        ConfigKey(
            name='APP_SECRET_KEY',
            key_type='str',
            default=os.urandom(24),
            mask=True,
            group='dev',
        ),
        ConfigKey(
            name='REDIS_URL',
            default='redis://localhost:6379/0',
            group='dev',
        ),
        ConfigKey(
            name='POSTMARK_API_KEY',
            key_type='str',
            default=None,
            mask=True,
            group='dev',
        ),
        ConfigKey(
            name='AUTH0_DOMAIN',
            key_type='str',
            default=None,
            group='dev',
        ),
        ConfigKey(
            name='AUTH0_CLIENT_ID',
            key_type='str',
            default=None,
            mask=True,
            group='dev',
        ),
        ConfigKey(
            name='AUTH0_CLIENT_SECRET',
            key_type='str',
            default=None,
            mask=True,
            group='dev',
        ),
        ConfigKey(
            name='PYPI_TOKEN',
            key_type='str',
            default=None,
            mask=True,
            group='dev',
        ),
    ],
)
