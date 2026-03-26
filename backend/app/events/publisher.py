import logging

from app.core.redis import publish

logger = logging.getLogger(__name__)


def publish_message_created(redis_client, payload: dict):
    # payload must include keys: message_id, session_id, patient_id, content, sender
    try:
        # publisher helper delegates to Redis and logs failures internally
        publish("message.created", payload)
        logger.info("Event message.created published: %s", payload)
    except Exception:
        # publish helper already logs; keep this safe and continue
        logger.exception("Failed to publish message.created event")
