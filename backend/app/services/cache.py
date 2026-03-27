import json
import logging

from sqlalchemy import select

from app.models.messages import Message

logger = logging.getLogger(__name__)


async def get_session_messages(session_id: str, redis_client, db):
    key = f"session:{session_id}:messages"
    serialized = await redis_client.get(key)
    if serialized:
        try:
            messages = json.loads(serialized)
            logger.info("Cache hit for session %s", session_id)
            return messages
        except Exception:
            logger.exception(
                "Failed to deserialize cached session messages for %s", session_id
            )

    # Cache miss: load from DB
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(10)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    messages = [
        {
            "id": str(r.id),
            "session_id": str(r.session_id),
            "sender": r.sender,
            "content": r.content,
            "emotion_label": r.emotion_label,
            "emotion_score": r.emotion_score,
            "danger_flag": r.danger_flag,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

    try:
        await redis_client.set(key, json.dumps(messages), ex=3600)
    except Exception:
        logger.exception("Failed to set cache for session %s", session_id)

    return messages


async def set_session_messages(session_id: str, messages, redis_client):
    key = f"session:{session_id}:messages"
    try:
        await redis_client.set(key, json.dumps(messages), ex=3600)
        logger.info("Cache set for session %s", session_id)
    except Exception:
        logger.exception("Failed to set session cache for %s", session_id)


async def invalidate_session_messages(session_id: str, redis_client):
    key = f"session:{session_id}:messages"
    try:
        await redis_client.delete(key)
        logger.info("Cache invalidated for session %s", session_id)
    except Exception:
        logger.exception("Failed to invalidate session cache for %s", session_id)
