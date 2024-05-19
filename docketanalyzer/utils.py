from datetime import datetime, date
from dateutil.parser._parser import ParserError
import pandas as pd
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from pathlib import Path
import regex as re
from docketanalyzer import config


# Configuration
DATA_DIR = config['DA_DATA_DIR']
COURTLISTENER_TOKEN = config['COURTLISTENER_TOKEN']
PACER_USERNAME = config['PACER_USERNAME']
PACER_PASSWORD = config['PACER_PASSWORD']
HF_TOKEN = config['HF_TOKEN']
GROQ_API_KEY = config['GROQ_API_KEY']
GROQ_DEFAULT_CHAT_MODEL = config['GROQ_DEFAULT_CHAT_MODEL']
OPENAI_API_KEY = config['OPENAI_API_KEY']
OPENAI_ORG_ID = config['OPENAI_ORG_ID']
OPENAI_DEFAULT_CHAT_MODEL = config['OPENAI_DEFAULT_CHAT_MODEL']
OPENAI_DEFAULT_EMBEDDING_MODEL = config['OPENAI_DEFAULT_EMBEDDING_MODEL']
POSTGRES_HOST = config['POSTGRES_HOST']
POSTGRES_PORT = config['POSTGRES_PORT']
POSTGRES_USERNAME = config['POSTGRES_USERNAME']
POSTGRES_PASSWORD = config['POSTGRES_PASSWORD']
POSTGRES_DB = config['POSTGRES_DB']
ELASTIC_URL = config['ELASTIC_URL']
AWS_ACCESS_KEY_ID = config['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = config['AWS_SECRET_ACCESS_KEY']
AWS_S3_BUCKET_NAME = config['AWS_S3_BUCKET_NAME']
AWS_S3_ENDPOINT_URL = config['AWS_S3_ENDPOINT_URL']
AWS_S3_REGION_NAME = config['AWS_S3_REGION_NAME']

# Other Utilities
def notabs(text):
    return '\n'.join([x.strip() for x in text.split('\n')]).strip()


def convert_date(x):
    if x:
        try:
            return pd.to_datetime(x).date()
        except (ParserError, OutOfBoundsDatetime):
            pass


def convert_int(x):
    if x is not None:
        try:
            return int(x)
        except ValueError:
            pass


def json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()


def pd_save_or_append(data, path, **kwargs):
    path = Path(path)
    if path.exists():
        data.to_csv(path, mode='a', header=False, index=False, **kwargs)
    else:
        data.to_csv(path, index=False, **kwargs)


def get_clean_name(name):
    return re.sub(r"[,.;@#?!&$]+\ *", " ", name.lower()).strip()
