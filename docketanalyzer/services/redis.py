from redis import Redis

from docketanalyzer import env

from .service import Service


class RedisService(Service):
    """Redis service class."""

    name = "redis"

    def init(self):
        """Initialize the Redis service."""
        host = env.REDIS_HOST or env.APP_HOST
        port = env.REDIS_PORT
        return Redis.from_url(f"redis://{host}:{port}/0")

    def close(self):
        """Close the Redis connection."""
        self.client.close()

    def status(self):
        """Check if the Redis is connected."""
        return self.client.ping()
