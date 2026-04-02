import asyncio
import json
import logging
import os
import sys

import redis.asyncio as redis

from app.db.session import AsyncSessionLocal

# Configure logging to output to stdout so docker can see it
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


class WorkerBase:
    def __init__(self, channel: str, redis_url: str = ""):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.channel = channel

    async def connect_redis(self):
        while True:
            try:
                client = redis.from_url(self.redis_url)
                await client.ping()
                logger.info("Worker started, subscribing to %s", self.channel)
                return client
            except Exception as e:
                logger.exception("Redis connection failed: %s", e)
                await asyncio.sleep(5)

    async def _dispatch(self, payload: dict):
        async with AsyncSessionLocal() as db:
            await self.handle_payload(payload, db)

    async def process_message(self, payload: dict):
        try:
            await self._dispatch(payload)
        except Exception as e:
            logger.exception("Failed to process payload: %s", e)

    async def run(self):
        redis_client = await self.connect_redis()
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(self.channel)

        try:
            async for message in pubsub.listen():
                try:
                    data = message.get("data")
                    if data is None or message.get("type") == "subscribe":
                        continue
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    payload = json.loads(data)
                    logger.info("Received event on %s: %s", self.channel, payload)
                    await self.process_message(payload)
                except Exception as e:
                    logger.exception("Failed to process message: %s", e)
        except KeyboardInterrupt:
            logger.info("Worker shutting down")
        except Exception as e:
            logger.exception("Worker error: %s", e)
        finally:
            pubsub.close()
            redis_client.close()

    async def handle_payload(self, payload: dict, db):
        raise NotImplementedError("handle_payload must be implemented in subclass")
