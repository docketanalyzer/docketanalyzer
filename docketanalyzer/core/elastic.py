from elasticsearch import Elasticsearch
from docketanalyzer import env


def load_elastic(**kwargs):
    """Load an Elasticsearch client with the configured connection URL.

    Run `da configure elastic` to set the connection URL.
    """
    es = Elasticsearch(env.ELASTIC_URL, **kwargs)
    return es
