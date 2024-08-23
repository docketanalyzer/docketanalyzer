from elasticsearch import Elasticsearch
from docketanalyzer.utils import ELASTIC_URL


def load_elastic(**kwargs):
    es = Elasticsearch(ELASTIC_URL, **kwargs)
    return es
