import os
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

