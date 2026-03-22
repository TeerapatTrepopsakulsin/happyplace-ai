import json
import logging
import os

import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_redis_client = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


async def get_redis():
    redis_client = get_redis_client()
    return redis_client


async def publish(channel: str, payload: dict):
    redis_client = get_redis_client()
    try:
        body = json.dumps(payload)
        await redis_client.publish(channel, body)
        logger.info("Published to Redis channel %s", channel)
    except Exception as e:
        logger.exception("Failed to publish to Redis channel %s: %s", channel, e)
