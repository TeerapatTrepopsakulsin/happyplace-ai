from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
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
from app.services.chat_service import get_guidelines, build_system_prompt, get_conversation_history, call_groq, update_session_cache
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(desc(ChatSession.last_active))
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [
        SessionResponse(
            id=str(s.id),
            title=s.title,
            created_at=s.created_at.isoformat(),
            last_active=s.last_active.isoformat() if s.last_active else None
        ) for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db)
):
    session = ChatSession(user_id=current_user.id, title="New conversation")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=str(session.id),
        title=session.title,
        created_at=session.created_at.isoformat(),
        last_active=None
    )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
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
            Invitation.invitee_id == current_user.id
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
            created_at=m["created_at"]
        ) for m in messages
    ]

