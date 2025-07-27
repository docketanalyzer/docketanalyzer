from elasticsearch import Elasticsearch

from docketanalyzer import env

from .service import Service


class ElasticService(Service):
    """Elastic service class."""

    name = "es"

    def init(self):
        """Initialize the Elastic service."""
        host = env.ELASTIC_HOST or env.APP_HOST
        port = env.ELASTIC_PORT
        return Elasticsearch(f"http://{host}:{port}")

    def close(self):
        """Close the Elastic connection."""
        self.client.close()

    def status(self):
        """Check if the Elastic is connected."""
        return self.client.ping()
