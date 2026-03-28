from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.users import User
from app.models.invitations import Invitation

router = APIRouter()


class InvitationCreateRequest(BaseModel):
    invitee_email: str


class InvitationResponse(BaseModel):
    id: str
    invitee_email: str
    invitee_display_name: str | None
    role_granted: str
    created_at: str  # datetime as string


class InvitationListResponse(BaseModel):
    id: str
    invitee_email: str
    invitee_display_name: str | None
    role_granted: str
    created_at: str  # datetime as string


@router.post(
    "/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    request: InvitationCreateRequest,
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
):
    # Look up user by email
    user_stmt = select(User).where(User.email == request.invitee_email)
    user_result = await db.execute(user_stmt)
    invitee = user_result.scalar_one_or_none()
    if not invitee:
        raise HTTPException(status_code=404, detail="No user found with this email")

    # Check invitee role
    if invitee.role == "regular":
        raise HTTPException(
            status_code=400, detail="Cannot invite a patient as a monitor"
        )

    # Check if invitation already exists
    existing_stmt = select(Invitation).where(
        and_(
            Invitation.sender_id == current_user.id, Invitation.invitee_id == invitee.id
        )
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400, detail="This user has already been invited"
        )

    # Create invitation
    invitation = Invitation(sender_id=current_user.id, invitee_id=invitee.id)
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return InvitationResponse(
        id=str(invitation.id),
        invitee_email=str(invitee.email),
        invitee_display_name=str(invitee.display_name),
        role_granted=str(invitee.role),  # derived from invitee's role
        created_at=str(invitation.created_at),
    )


@router.get("/invitations", response_model=List[InvitationListResponse])
async def get_invitations(
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
):
    # Get all invitations sent by current user
    stmt = (
        select(Invitation, User)
        .join(User, Invitation.invitee_id == User.id)
        .where(Invitation.sender_id == current_user.id)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    return [
        InvitationListResponse(
            id=str(invitation.id),
            invitee_email=user.email,
            invitee_display_name=user.display_name,
            role_granted=user.role,
            created_at=str(invitation.created_at),
        )
        for invitation, user in rows
    ]


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invitation(
    invitation_id: str,
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
):
    # Get the invitation
    stmt = select(Invitation).where(Invitation.id == invitation_id)
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    # Verify it belongs to current user
    if invitation.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete
    await db.delete(invitation)
    await db.commit()
