from playhouse.pool import PooledPostgresqlExtDatabase

from docketanalyzer import env

from .service import Service


class PostgresService(Service):
    """Postgres service class."""

    name = "db"

    def init(self):
        """Initialize the Postgres service."""
        host = env.POSTGRES_HOST or env.APP_HOST
        return PooledPostgresqlExtDatabase(
            database=env.POSTGRES_DB,
            user=env.POSTGRES_USER,
            password=env.POSTGRES_PASSWORD,
            host=host,
            port=env.POSTGRES_PORT,
            max_connections=32,
            stale_timeout=300,
            timeout=0,
        )

    def close(self):
        """Close the database connection."""
        self.client.close()

    def status(self):
        """Check if the database is connected."""
        return self.client.connect(reuse_if_open=True) is not None
