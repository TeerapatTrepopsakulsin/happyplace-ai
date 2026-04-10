from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.users import User
from app.schemas import (
    InvitationCreateRequest,
    InvitationListResponse,
    InvitationResponse,
)
from app.services.invitation_service import (
    create_invitation_for_user,
    delete_invitation_for_user,
    list_invitations_for_user,
)

router = APIRouter()


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
    invitation, invitee = await create_invitation_for_user(
        request.invitee_email, current_user, db
    )

    return InvitationResponse(
        id=str(invitation.id),
        invitee_email=str(invitee.email),
        invitee_display_name=str(invitee.display_name),
        role_granted=str(invitee.role),
        created_at=str(invitation.created_at),
    )


@router.get("/invitations", response_model=List[InvitationListResponse])
async def get_invitations(
    current_user: User = Depends(require_role("regular")),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_invitations_for_user(current_user, db)
    return [
        InvitationListResponse(
            id=str(invitation.id),
            invitee_email=str(user.email),
            invitee_display_name=str(user.display_name),
            role_granted=str(user.role),
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
    await delete_invitation_for_user(invitation_id, current_user, db)
