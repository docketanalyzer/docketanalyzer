from elasticsearch import Elasticsearch
from docketanalyzer.utils import ELASTIC_HOST, ELASTIC_PORT, ELASTIC_USERNAME, ELASTIC_PASSWORD


def load_elastic(**kwargs):
    return Elasticsearch(
        f"http://{ELASTIC_HOST}:{ELASTIC_PORT}",
        basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD),
        **kwargs,
    )
