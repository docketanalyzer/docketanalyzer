import json
import time

import peewee
from redis import Redis

from docketanalyzer import CACHE_DIR, env

from .service import Service


class RedisKey(peewee.Model):
    """A Peewee model for storing Redis-like data."""

    key = peewee.CharField(primary_key=True)
    value = peewee.TextField()
    expiry = peewee.FloatField(null=True)


class DevRedisClient:
    """A dev-only Redis replacement that uses SQLite for persistence."""

    def __init__(self, db_path: str | None = None, clear_on_init: bool = True):
        """Initialize the DevRedisClient."""
        if db_path is None:
            db_path = CACHE_DIR / "redis.db"
        self.db = peewee.SqliteDatabase(db_path)
        RedisKey._meta.database = self.db

        self.db.connect()
        self.db.create_tables([RedisKey], safe=True)

        if clear_on_init:
            self.clean_up()

    def _check_expiry(self, redis_key: RedisKey) -> bool:
        """Check if a key has expired."""
        if redis_key.expiry is None:
            return True

        if time.time() > redis_key.expiry:
            redis_key.delete_instance()
            return False

        return True

    def clean_up(self):
        """Clean up expired keys."""
        current_time = time.time()
        RedisKey.delete().where(
            (RedisKey.expiry.is_null(False)) & (RedisKey.expiry < current_time)
        ).execute()

    def get(self, key: str) -> str | None:
        """Get the value of a key."""
        try:
            redis_key = RedisKey.get(RedisKey.key == key)

            if not self._check_expiry(redis_key):
                return None

            return redis_key.value
        except RedisKey.DoesNotExist:
            return None

    def set(
        self,
        key: str,
        value: str | int | float | dict | list,
        ex: int | None = None,
    ) -> bool:
        """Set the value of a key."""
        value_str = json.dumps(value) if isinstance(value, dict | list) else str(value)

        expiry = ex if ex is None else time.time() + ex

        RedisKey.insert(key=key, value=value_str, expiry=expiry).on_conflict(
            conflict_target=[RedisKey.key],
            update={RedisKey.value: value_str, RedisKey.expiry: expiry},
        ).execute()

        return True

    def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if not keys:
            return 0

        count = RedisKey.select().where(RedisKey.key.in_(keys)).count()

        RedisKey.delete().where(RedisKey.key.in_(keys)).execute()

        return count

    def exists(self, *keys: str) -> int:
        """Check if one or more keys exist."""
        if not keys:
            return 0

        count = 0
        for key in keys:
            try:
                redis_key = RedisKey.get(RedisKey.key == key)
                if self._check_expiry(redis_key):
                    count += 1
            except RedisKey.DoesNotExist:
                pass

        return count

    def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching a pattern."""
        current_time = time.time()
        RedisKey.delete().where(
            (RedisKey.expiry.is_null(False)) & (RedisKey.expiry < current_time)
        ).execute()

        if pattern == "*":
            query = RedisKey.select()
        elif pattern.startswith("*") and pattern.endswith("*"):
            search_term = pattern[1:-1]
            query = RedisKey.select().where(RedisKey.key.contains(search_term))
        elif pattern.startswith("*"):
            search_term = pattern[1:]
            query = RedisKey.select().where(RedisKey.key.endswith(search_term))
        elif pattern.endswith("*"):
            search_term = pattern[:-1]
            query = RedisKey.select().where(RedisKey.key.startswith(search_term))
        else:
            query = RedisKey.select().where(RedisKey.key == pattern)

        return [redis_key.key for redis_key in query]

    def ping(self):
        """Mock ping the Redis server."""
        return True

    def close(self):
        """Close the database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


class RedisService(Service):
    """Redis service class."""

    name = "redis"

    def init(self):
        """Initialize the Redis service."""
        if not env.REDIS_HOST:
            return DevRedisClient()

        host = env.REDIS_HOST
        port = env.REDIS_PORT
        return Redis.from_url(f"redis://{host}:{port}/0")

    def close(self):
        """Close the Redis connection."""
        self.client.close()

    def status(self):
        """Check if the Redis is connected."""
        return self.client.ping()
