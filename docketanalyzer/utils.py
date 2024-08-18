from datetime import datetime, date
from dateutil.parser._parser import ParserError
import os
import signal
import numpy as np
import pandas as pd
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from pathlib import Path
import regex as re
from docketanalyzer.config import config


# Configuration
DATA_DIR = config['DA_DATA_DIR']
COURTLISTENER_TOKEN = config['COURTLISTENER_TOKEN']
PACER_USERNAME = config['PACER_USERNAME']
PACER_PASSWORD = config['PACER_PASSWORD']
HF_TOKEN = config['HF_TOKEN']
ANTHROPIC_API_KEY = config['ANTHROPIC_API_KEY']
ANTHROPIC_DEFAULT_CHAT_MODEL = config['ANTHROPIC_DEFAULT_CHAT_MODEL']
GROQ_API_KEY = config['GROQ_API_KEY']
GROQ_DEFAULT_CHAT_MODEL = config['GROQ_DEFAULT_CHAT_MODEL']
OPENAI_API_KEY = config['OPENAI_API_KEY']
OPENAI_ORG_ID = config['OPENAI_ORG_ID']
OPENAI_DEFAULT_CHAT_MODEL = config['OPENAI_DEFAULT_CHAT_MODEL']
OPENAI_DEFAULT_EMBEDDING_MODEL = config['OPENAI_DEFAULT_EMBEDDING_MODEL']
COHERE_API_KEY = config['COHERE_API_KEY']
COHERE_DEFAULT_CHAT_MODEL = config['COHERE_DEFAULT_CHAT_MODEL']
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
SELENIUM_HOST = config['SELENIUM_HOST']
SELENIUM_PORT = config['SELENIUM_PORT']
WEB_SEARCH_PORT = config['WEB_SEARCH_PORT']
PYPI_TOKEN = config['PYPI_TOKEN']
BUILD_MODE = os.environ.get('BUILD_MODE', False)


# Other Utilities
def configure(vars):
    setting2name = {
        'DATA_DIR': 'DA_DATA_DIR',
    }
    name2setting = {v: k for k, v in setting2name.items()}
    names = config.names
    for k, v in vars.items():
        if k in names or setting2name.get(k) in names:
            if k in name2setting:
                k = name2setting[k]
            globals()[k] = v
        else:
            print(f"Skipping invalid setting: {k}")


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


def list_to_array(embeddings):
    return np.array([np.array(e) for e in embeddings]).astype('float32')


def pd_save_or_append(data, path, **kwargs):
    path = Path(path)
    if path.exists():
        data.to_csv(path, mode='a', header=False, index=False, **kwargs)
    else:
        data.to_csv(path, index=False, **kwargs)


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)


class timeit:
    def __init__(self, tag='Task'):
        self.tag = tag
        self.start = None

    def __enter__(self):
        self.start = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = datetime.now()
        execution_time = (end - self.start).total_seconds()
        print(f"{self.tag} took {execution_time:.4f} seconds")


def lazy_load(import_path, object_name):
    class LazyObject():
        cache = {}
        import_path = None
        object_name = None

        def __new__(cls, *args, **kwargs):
            if len(args) == 3 and isinstance(args[1], tuple):
                child_name, (lazy_parent,), child_attrs = args
                parent_cls = cls.cls_object()
                new_cls = type(child_name, (parent_cls,), child_attrs)
                return new_cls
            return super().__new__(cls)
        
        @classmethod
        def cls_object(cls):
            if 'object' not in cls.cache:
                module = __import__(cls.import_path, fromlist=[cls.object_name])
                cls.cache['object'] = getattr(module, cls.object_name)
            return cls.cache['object']

        @property
        def object(self):
            return type(self).cls_object()
            
        def __call__(self, *args, **kwargs):
            return self.object(*args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.object, name)
        
        @classmethod
        def __instancecheck__(cls, instance):
            return isinstance(instance, cls.cls_object())

        @classmethod
        def __subclasscheck__(cls, subclass):
            return issubclass(subclass, cls.cls_object())
    
    LazyObject.import_path = import_path
    LazyObject.object_name = object_name
    return LazyObject()


# Extraction Utilities
def extract_from_pattern(text, pattern, label, ignore_case=False, extract_groups={}):
    spans = []
    for match in re.finditer(pattern, text, re.IGNORECASE if ignore_case else 0):
        spans.append({
            'start': match.start(),
            'end': match.end(),
            'name': label,
        })
        for k, v in extract_groups.items():
            spans[-1][k] = match.group(v)
    return spans


def extract_attachments(text):
    pattern = r'((\(|\( )?(EXAMPLE: )?(additional )?Attachment\(?s?\)?([^:]+)?: )((([^()]+)?(\(([^()]+|(?7))*+\))?([^()]+)?)*+)\)*+'
    spans = extract_from_pattern(
        text, pattern,
        'attachment_section',
        ignore_case=True,
        extract_groups={'attachments': 6}
    )
    for span in spans:
        attachments = {}
        for attachment in re.findall(r'# (\d+) ([^#]+?)(?=, #|#|$)', span['attachments']):
            attachments[int(attachment[0])] = attachment[1]
        span['attachments'] = attachments
    return spans


def extract_entered_date(text):
    pattern = r'\(Entered: ([\d]+/[\d]+/[\d]+)\)'
    return extract_from_pattern(text, pattern, 'entered_date')


def get_clean_name(name):
    return re.sub(r"[,.;@#?!&$]+\ *", " ", name.lower()).strip()


def mask_text_with_spans(text, spans, mapper=None):
    if mapper is None:
        mapper = lambda text, span: f"<{span['label']}>"
    spans = sorted(spans, key=lambda x: -x['start'])
    for span in spans:
        span_replace = mapper(text, span)
        text = text[:span['start']] + span_replace + text[span['end']:]
    return text
