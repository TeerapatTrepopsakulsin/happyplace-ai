from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.publisher import publish_message_created
from app.models.chat_sessions import ChatSession
from app.models.invitations import Invitation
from app.models.messages import Message
from app.models.users import User
from app.services.cache import get_session_messages
from app.services.chatbot_service import (
    build_system_prompt,
    call_groq,
    get_conversation_history,
    get_guidelines,
    update_session_cache,
)
from app.services.errors import ExternalServiceError, ForbiddenError, NotFoundError


async def _get_user_owned_session(
    session_id: str, current_user: User, db: AsyncSession
) -> ChatSession:
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise ForbiddenError("Access denied")
    return session


async def _get_accessible_session(
    session_id: str, current_user: User, db: AsyncSession
) -> ChatSession:
    session = await db.get(ChatSession, session_id)
    if not session:
        raise NotFoundError("Session not found")

    if session.user_id == current_user.id:
        return session

    if current_user.role in ["therapist", "guardian"]:
        stmt = select(Invitation).where(
            Invitation.sender_id == session.user_id,
            Invitation.invitee_id == current_user.id,
        )
        result = await db.execute(stmt)
        invitation = result.scalar_one_or_none()
        if invitation:
            return session

    raise ForbiddenError("Access denied")


async def list_messages_for_session(
    session_id: str, current_user: User, db: AsyncSession, redis_client
) -> list[dict]:
    await _get_accessible_session(session_id, current_user, db)
    messages = await get_session_messages(session_id, redis_client, db)
    return list(messages)


async def send_message_for_user(
    session_id: str,
    content: str,
    current_user: User,
    db: AsyncSession,
    redis_client,
) -> dict:
    session = await _get_user_owned_session(session_id, current_user, db)

    user_msg = Message(
        session_id=session_id,
        sender="user",
        content=content,
        emotion_label=None,
        emotion_score=None,
        danger_flag=False,
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    history = await get_conversation_history(session_id, redis_client, db)
    guidelines = await get_guidelines(current_user.id, db)
    system_prompt = build_system_prompt(guidelines)
    try:
        assistant_content = await call_groq(system_prompt, history, content)
    except Exception:
        raise ExternalServiceError("LLM service unavailable")

    assistant_msg = Message(
        session_id=session_id,
        sender="assistant",
        content=assistant_content,
        emotion_label=None,
        emotion_score=None,
        danger_flag=False,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    if assistant_msg.created_at:
        session.last_active = assistant_msg.created_at
    else:
        session.last_active = datetime.now(timezone.utc).replace(tzinfo=None)  # type: ignore[assignment]
    db.add(session)
    await db.commit()
    await db.refresh(session)

    await update_session_cache(session_id, redis_client, db)

    payload = {
        "message_id": str(user_msg.id),
        "session_id": session_id,
        "patient_id": str(current_user.id),
        "content": user_msg.content,
        "sender": "user",
    }
    await publish_message_created(redis_client, payload)

    return {
        "user_message": {
            "id": str(user_msg.id),
            "sender": str(user_msg.sender),
            "content": str(user_msg.content),
            "emotion_label": str(user_msg.emotion_label),
            "emotion_score": float(user_msg.emotion_score)
            if user_msg.emotion_score is not None
            else None,
            "danger_flag": bool(user_msg.danger_flag),
            "created_at": user_msg.created_at.isoformat(),
        },
        "assistant_message": {
            "id": str(assistant_msg.id),
            "sender": str(assistant_msg.sender),
            "content": str(assistant_msg.content),
            "emotion_label": str(assistant_msg.emotion_label),
            "emotion_score": 0.0,
            "danger_flag": bool(assistant_msg.danger_flag),
            "created_at": assistant_msg.created_at.isoformat(),
        },
    }
