from sqlalchemy import and_, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_sessions import ChatSession
from app.models.invitations import Invitation
from app.models.messages import Message
from app.models.users import User
from app.services.errors import ForbiddenError


def _to_session_dict(session: ChatSession) -> dict:
    return {
        "id": str(session.id),
        "title": str(session.title),
        "created_at": session.created_at.isoformat(),
        "last_active": session.last_active.isoformat() if session.last_active else None,
    }


async def _verify_monitor_access_to_patient(
    patient_id: str, current_user: User, db: AsyncSession
) -> None:
    invitation_stmt = select(Invitation).where(
        and_(
            Invitation.sender_id == patient_id,
            Invitation.invitee_id == current_user.id,
        )
    )
    invitation_result = await db.execute(invitation_stmt)
    invitation = invitation_result.scalar_one_or_none()
    if not invitation:
        raise ForbiddenError("Access denied")


async def list_sessions_for_user(current_user: User, db: AsyncSession) -> list[dict]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.last_active))
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [_to_session_dict(s) for s in sessions]


async def list_sessions_for_patient(
    patient_id: str, current_user: User, db: AsyncSession
) -> list[dict]:
    await _verify_monitor_access_to_patient(patient_id, current_user, db)
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == patient_id)
        .order_by(desc(ChatSession.last_active))
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [_to_session_dict(s) for s in sessions]


async def create_session_for_user(current_user: User, db: AsyncSession) -> dict:
    session = ChatSession(user_id=current_user.id, title="New conversation")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _to_session_dict(session)


async def update_session_for_user(
    session_id: str, title: str, current_user: User, db: AsyncSession
) -> dict:
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise ForbiddenError("Access denied")

    session.title = title  # type: ignore[assignment]
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _to_session_dict(session)


async def delete_session_for_user(
    session_id: str, current_user: User, db: AsyncSession
) -> None:
    session = await db.get(ChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise ForbiddenError("Access denied")

    delete_stmt = delete(Message).where(Message.session_id == session_id)
    await db.execute(delete_stmt)
    await db.delete(session)
    await db.commit()
