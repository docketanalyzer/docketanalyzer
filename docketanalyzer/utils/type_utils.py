from datetime import datetime, date
from dateutil.parser._parser import ParserError
from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime


def list_to_array(embeddings):
    return np.array([np.array(e) for e in embeddings]).astype('float32')


def to_date(x):
    if x:
        try:
            return pd.to_datetime(x).date()
        except (ParserError, OutOfBoundsDatetime):
            pass


def to_int(x):
    if x is not None:
        try:
            return int(x)
        except ValueError:
            pass


def json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()