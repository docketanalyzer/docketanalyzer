from datetime import datetime, date
from dateutil.parser._parser import ParserError
import numpy as np
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
TOGETHER_API_KEY = config['TOGETHER_API_KEY']
TOGETHER_DEFAULT_CHAT_MODEL = config['TOGETHER_DEFAULT_CHAT_MODEL']
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


# Docket Utilities
def get_entries(docket_ids, add_shuffle_number=False):
    from docketanalyzer import DocketManager

    data = []
    for docket_id in docket_ids:
        manager = DocketManager(docket_id)
        docket_json = manager.docket_json
        if docket_json:
            entries = pd.DataFrame(docket_json['docket_entries'])
            if len(entries):
                entries['docket_id'] = docket_id
                entries['row_number'] = range(len(entries))
                if add_shuffle_number:
                    entries['shuffle_number'] = np.random.permutation(len(entries))
                data.append(entries)
    if not len(data):
        return None
    data = pd.concat(data)
    data['entry_id'] = data.apply(lambda x: f"{x['docket_id']}__{x['row_number']}", axis=1)
    data['date_filed'] = pd.to_datetime(data['date_filed'], errors='coerce')
    data['pacer_doc_id'] = data['pacer_doc_id'].astype(pd.Int64Dtype())
    data['document_number'] = data['document_number'].astype(pd.Int64Dtype())
    data['pacer_seq_no'] = data['pacer_seq_no'].astype(pd.Int64Dtype())
    data['date_entered'] = pd.to_datetime(data['date_entered'], errors='coerce')
    return data



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
