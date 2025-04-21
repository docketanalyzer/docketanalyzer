from redis import Redis

from .. import env


def load_redis(**kwargs):
    """Load a Redis client with the configured connection URL.

    Run `da configure elastic` to set the connection URL.
    """
    redis = Redis.from_url(env.REDIS_URL)
    return redis
