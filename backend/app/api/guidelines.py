from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.users import User
from app.models.invitations import Invitation
from app.models.chatbot_guidelines import ChatbotGuidelines

router = APIRouter()


class GuidelinesResponse(BaseModel):
    id: str
    patient_id: str
    authored_by: str
    response_tone: str | None
    coping_strategies: str | None
    behavioral_boundaries: str | None
    sensitive_topics: List[str] | None
    updated_at: str  # datetime as string


class GuidelinesUpdateRequest(BaseModel):
    response_tone: str | None = None
    coping_strategies: str | None = None
    behavioral_boundaries: str | None = None
    sensitive_topics: List[str] | None = None


@router.get("/guidelines/{patient_id}", response_model=GuidelinesResponse)
async def get_guidelines(
    patient_id: str,
    current_user: User = Depends(require_role("therapist")),
    db: AsyncSession = Depends(get_db),
):
    # Verify invitation
    invitation_stmt = select(Invitation).where(
        and_(
            Invitation.sender_id == patient_id, Invitation.invitee_id == current_user.id
        )
    )
    invitation_result = await db.execute(invitation_stmt)
    invitation = invitation_result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get guidelines
    stmt = select(ChatbotGuidelines).where(ChatbotGuidelines.user_id == patient_id)
    result = await db.execute(stmt)
    guidelines = result.scalar_one_or_none()
    if not guidelines:
        raise HTTPException(status_code=404, detail="Guidelines not found")

    return GuidelinesResponse(
        id=str(guidelines.id),
        patient_id=str(guidelines.user_id),
        authored_by=str(guidelines.authored_by),
        response_tone=str(guidelines.response_tone)
        if guidelines.response_tone
        else None,
        coping_strategies=str(guidelines.coping_strategies)
        if guidelines.coping_strategies
        else None,
        behavioral_boundaries=str(guidelines.behavioral_boundaries)
        if guidelines.behavioral_boundaries
        else None,
        sensitive_topics=[str(topic) for topic in guidelines.sensitive_topics]
        if guidelines.sensitive_topics
        else None,
        updated_at=str(guidelines.updated_at),
    )


@router.put("/guidelines/{patient_id}", response_model=GuidelinesResponse)
async def update_guidelines(
    patient_id: str,
    request: GuidelinesUpdateRequest,
    current_user: User = Depends(require_role("therapist")),
    db: AsyncSession = Depends(get_db),
):
    # Verify invitation
    invitation_stmt = select(Invitation).where(
        and_(
            Invitation.sender_id == patient_id, Invitation.invitee_id == current_user.id
        )
    )
    invitation_result = await db.execute(invitation_stmt)
    invitation = invitation_result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=403, detail="Access denied")

    # Upsert guidelines
    from sqlalchemy.dialects.postgresql import insert

    insert_stmt = insert(ChatbotGuidelines).values(
        user_id=patient_id,
        authored_by=str(current_user.id),
        response_tone=request.response_tone,
        coping_strategies=request.coping_strategies,
        behavioral_boundaries=request.behavioral_boundaries,
        sensitive_topics=request.sensitive_topics,
    )
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["user_id"],
        set_={
            "authored_by": str(current_user.id),
            "response_tone": request.response_tone,
            "coping_strategies": request.coping_strategies,
            "behavioral_boundaries": request.behavioral_boundaries,
            "sensitive_topics": request.sensitive_topics,
            "updated_at": text("now()"),
        },
    )
    await db.execute(upsert_stmt)
    await db.commit()

    # Fetch the updated/inserted record
    stmt = select(ChatbotGuidelines).where(ChatbotGuidelines.user_id == patient_id)
    result = await db.execute(stmt)
    guidelines = result.scalar_one()

    return GuidelinesResponse(
        id=str(guidelines.id),
        patient_id=str(guidelines.user_id),
        authored_by=str(guidelines.authored_by),
        response_tone=str(guidelines.response_tone)
        if guidelines.response_tone
        else None,
        coping_strategies=str(guidelines.coping_strategies)
        if guidelines.coping_strategies
        else None,
        behavioral_boundaries=str(guidelines.behavioral_boundaries)
        if guidelines.behavioral_boundaries
        else None,
        sensitive_topics=[str(topic) for topic in guidelines.sensitive_topics]
        if guidelines.sensitive_topics
        else None,
        updated_at=str(guidelines.updated_at),
    )
