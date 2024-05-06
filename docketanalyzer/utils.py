import os
from dateutil.parser._parser import ParserError
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime


load_dotenv(override=True)


default_data_dir = Path.home() / 'docketanalyzer'
DATA_DIR = Path(os.environ.get(
    'DA_DATA_DIR', default_data_dir
))
if not DATA_DIR.exists():
    DATA_DIR = default_data_dir


COURTLISTENER_TOKEN = os.environ.get('COURTLISTENER_TOKEN')

PACER_USERNAME = os.environ.get('PACER_USERNAME')
PACER_PASSWORD = os.environ.get('PACER_PASSWORD')


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
