import asyncio
import json
import logging
import os
import time

import redis

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class WorkerBase:
    def __init__(self, channel: str, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.channel = channel

    def connect_redis(self):
        while True:
            try:
                client = redis.from_url(self.redis_url)
                client.ping()
                logger.info("Worker started, subscribing to %s", self.channel)
                return client
            except Exception as e:
                logger.exception("Redis connection failed: %s", e)
                time.sleep(5)

    async def _dispatch(self, payload: dict):
        async with AsyncSessionLocal() as db:
            await self.handle_payload(payload, db)

    def process_message(self, payload: dict):
        try:
            asyncio.run(self._dispatch(payload))
        except Exception as e:
            logger.exception("Failed to process payload: %s", e)

    def run(self):
        redis_client = self.connect_redis()
        pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(self.channel)

        try:
            for message in pubsub.listen():
                try:
                    data = message.get("data")
                    if data is None:
                        continue
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")

                    payload = json.loads(data)
                    logger.info("Received event on %s: %s", self.channel, payload)
                    self.process_message(payload)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.exception("Error handling message: %s", e)
                    continue
        except KeyboardInterrupt:
            logger.info("Worker shutting down")
        finally:
            pubsub.close()
            redis_client.close()

    async def handle_payload(self, payload: dict, db):
        raise NotImplementedError("handle_payload must be implemented in subclass")
