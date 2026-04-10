from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invitations import Invitation
from app.models.users import User
from app.services.errors import BadRequestError, ForbiddenError, NotFoundError


async def create_invitation_for_user(
    invitee_email: str, current_user: User, db: AsyncSession
) -> tuple[Invitation, User]:
    user_stmt = select(User).where(User.email == invitee_email)
    user_result = await db.execute(user_stmt)
    invitee = user_result.scalar_one_or_none()
    if not invitee:
        raise NotFoundError("No user found with this email")

    if invitee.role == "regular":
        raise BadRequestError("Cannot invite a patient as a monitor")

    existing_stmt = select(Invitation).where(
        and_(
            Invitation.sender_id == current_user.id, Invitation.invitee_id == invitee.id
        )
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise BadRequestError("This user has already been invited")

    invitation = Invitation(sender_id=current_user.id, invitee_id=invitee.id)
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    return invitation, invitee


async def list_invitations_for_user(
    current_user: User, db: AsyncSession
) -> list[tuple[Invitation, User]]:
    stmt = (
        select(Invitation, User)
        .join(User, Invitation.invitee_id == User.id)
        .where(Invitation.sender_id == current_user.id)
    )
    result = await db.execute(stmt)
    rows = result.tuples().all()

    return list(rows)


async def delete_invitation_for_user(
    invitation_id: str, current_user: User, db: AsyncSession
) -> None:
    stmt = select(Invitation).where(Invitation.id == invitation_id)
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise NotFoundError("Invitation not found")

    if invitation.sender_id != current_user.id:
        raise ForbiddenError("Access denied")

    await db.delete(invitation)
    await db.commit()
