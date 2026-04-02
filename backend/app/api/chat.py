from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.chat_sessions import ChatSession
from app.models.messages import Message
from app.models.invitations import Invitation
from app.models.users import User
from app.services.cache import get_session_messages
from app.services.chat_service import (
    get_guidelines,
    build_system_prompt,
    get_conversation_history,
    call_groq,
    update_session_cache,
)
from app.events.publisher import publish_message_created
from app.core.redis import get_redis


router = APIRouter(prefix="/api/v1/chat")


class SessionResponse(BaseModel):
    id: str
    title: str | None
    created_at: str
    last_active: str | None


class MessageResponse(BaseModel):
    id: str
    sender: str
    content: str
    emotion_label: str | None
    emotion_score: float | None
    danger_flag: bool
    created_at: str


class SendMessageRequest(BaseModel):
    content: str


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.last_active))
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [
        SessionResponse(
            id=str(s.id),
            title=str(s.title),
            created_at=s.created_at.isoformat(),
            last_active=s.last_active.isoformat() if s.last_active else None,
        )
        for s in sessions
    ]


@router.get("/patients/{patient_id}/sessions", response_model=List[SessionResponse])
async def get_patient_sessions(
    patient_id: str,
    current_user: User = Depends(require_role("therapist", "guardian")),
    db: AsyncSession = Depends(get_db),
):
    """Get sessions for a patient (requires therapist/guardian access)"""
    # Check if current user has access to this patient
    if current_user.role in ["therapist", "guardian"]:
        invitation_stmt = select(Invitation).where(
            and_(
                Invitation.sender_id == patient_id,
                Invitation.invitee_id == current_user.id,
            )
        )
        invitation_result = await db.execute(invitation_stmt)
        invitation = invitation_result.scalar_one_or_none()
        if not invitation:
            raise HTTPException(status_code=403, detail="Access denied")

    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == patient_id)
        .order_by(desc(ChatSession.last_active))
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [
        SessionResponse(
            id=str(s.id),
            title=str(s.title),
            created_at=s.created_at.isoformat(),
            last_active=s.last_active.isoformat() if s.last_active else None,
        )
        for s in sessions
    ]


@router.post(
    "/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
):
    session = ChatSession(user_id=current_user.id, title="New conversation")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=str(session.id),
        title=str(session.title),
        created_at=session.created_at.isoformat(),
        last_active=None,
    )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    # Get the session
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check ownership or invitation
    if session.user_id == current_user.id:
        pass  # ok
    elif current_user.role in ["therapist", "guardian"]:
        # Check invitation
        stmt = select(Invitation).where(
            Invitation.sender_id == session.user_id,
            Invitation.invitee_id == current_user.id,
        )
        result = await db.execute(stmt)
        invitation = result.scalar_one_or_none()
        if not invitation:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get messages
    messages = await get_session_messages(session_id, redis_client, db)
    return [
        MessageResponse(
            id=m["id"],
            sender=m["sender"],
            content=m["content"],
            emotion_label=m["emotion_label"],
            emotion_score=m["emotion_score"],
            danger_flag=m["danger_flag"],
            created_at=m["created_at"],
        )
        for m in messages
    ]


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    # Verify session belongs to current user
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 1. Persist user message
    user_msg = Message(
        session_id=session_id,
        sender="user",
        content=request.content,
        emotion_label=None,
        emotion_score=None,
        danger_flag=False,
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # 2. Get conversation history
    history = await get_conversation_history(session_id, redis_client, db)

    # 3. Get guidelines
    guidelines = await get_guidelines(current_user.id, db)

    # 4. Build system prompt
    system_prompt = build_system_prompt(guidelines)

    # 5. Call Groq
    try:
        assistant_content = await call_groq(system_prompt, history, request.content)
    except Exception:
        raise HTTPException(status_code=502, detail="LLM service unavailable")

    # 6. Persist assistant message
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

    # Update session last_active using the resolved assistant message timestamp
    if assistant_msg.created_at:
        session.last_active = assistant_msg.created_at
    else:
        from datetime import datetime

        session.last_active = datetime.utcnow()

    db.add(session)
    await db.commit()
    await db.refresh(session)

    # 7. Update session cache
    await update_session_cache(session_id, redis_client, db)

    # 8. Publish event (user message event is required for emotion/danger analysis)
    payload = {
        "message_id": str(user_msg.id),
        "session_id": session_id,
        "patient_id": str(current_user.id),
        "content": user_msg.content,
        "sender": "user",
    }
    await publish_message_created(redis_client, payload)

    # 9. Return response
    return SendMessageResponse(
        user_message=MessageResponse(
            id=str(user_msg.id),
            sender=str(user_msg.sender),
            content=str(user_msg.content),
            emotion_label=str(user_msg.emotion_label),
            emotion_score=float(user_msg.emotion_score)
            if user_msg.emotion_score is not None
            else None,
            danger_flag=bool(user_msg.danger_flag),
            created_at=user_msg.created_at.isoformat(),
        ),
        assistant_message=MessageResponse(
            id=str(assistant_msg.id),
            sender=str(assistant_msg.sender),
            content=str(assistant_msg.content),
            emotion_label=str(assistant_msg.emotion_label),
            emotion_score=0.0,
            danger_flag=bool(assistant_msg.danger_flag),
            created_at=assistant_msg.created_at.isoformat(),
        ),
    )
