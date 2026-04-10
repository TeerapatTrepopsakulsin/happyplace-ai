from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.users import User
from app.core.redis import get_redis
from app.schemas import (
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
    SessionResponse,
    SessionUpdateRequest,
)
from app.services.chat_message_service import (
    list_messages_for_session,
    send_message_for_user,
)
from app.services.chat_session_service import (
    create_session_for_user,
    delete_session_for_user,
    list_sessions_for_patient,
    list_sessions_for_user,
    update_session_for_user,
)


router = APIRouter(prefix="/api/v1/chat")


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    sessions = await list_sessions_for_user(current_user, db)
    return [SessionResponse(**s) for s in sessions]


@router.get("/patients/{patient_id}/sessions", response_model=List[SessionResponse])
async def get_patient_sessions(
    patient_id: str,
    current_user: User = Depends(require_role("therapist", "guardian")),
    db: AsyncSession = Depends(get_db),
):
    sessions = await list_sessions_for_patient(patient_id, current_user, db)
    return [SessionResponse(**s) for s in sessions]


@router.post(
    "/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
):
    session = await create_session_for_user(current_user, db)
    return SessionResponse(**session)


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
):
    session = await update_session_for_user(session_id, request.title, current_user, db)
    return SessionResponse(**session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
):
    await delete_session_for_user(session_id, current_user, db)
    return None


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    messages = await list_messages_for_session(
        session_id, current_user, db, redis_client
    )
    return [MessageResponse(**m) for m in messages]


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    response = await send_message_for_user(
        session_id, request.content, current_user, db, redis_client
    )
    return SendMessageResponse(
        user_message=MessageResponse(**response["user_message"]),
        assistant_message=MessageResponse(**response["assistant_message"]),
    )
