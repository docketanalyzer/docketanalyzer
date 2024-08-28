from elasticsearch import Elasticsearch
from docketanalyzer import ELASTIC_URL


def load_elastic(**kwargs):
    es = Elasticsearch(ELASTIC_URL, **kwargs)
    return es
