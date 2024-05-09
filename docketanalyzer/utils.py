from dateutil.parser._parser import ParserError
from dotenv import load_dotenv
import pandas as pd
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from docketanalyzer import config


load_dotenv(override=True)


# Configuration
DATA_DIR = config['DA_DATA_DIR']
COURTLISTENER_TOKEN = config['COURTLISTENER_TOKEN']
PACER_USERNAME = config['PACER_USERNAME']
PACER_PASSWORD = config['PACER_PASSWORD']
POSTGRES_HOST = config['POSTGRES_HOST']
POSTGRES_PORT = config['POSTGRES_PORT']
POSTGRES_USERNAME = config['POSTGRES_USERNAME']
POSTGRES_PASSWORD = config['POSTGRES_PASSWORD']
POSTGRES_DB = config['POSTGRES_DB']


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
