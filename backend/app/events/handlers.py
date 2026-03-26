import logging

logger = logging.getLogger(__name__)


async def handle_emotion(payload: dict, db):
    logger.info("handle_emotion received payload: %s", payload)
    # Stub: real analysis will be implemented later


async def handle_danger(payload: dict, db):
    logger.info("handle_danger received payload: %s", payload)
    # Stub: real danger keyword check will be implemented later
