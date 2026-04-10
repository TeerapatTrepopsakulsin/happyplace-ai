from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.users import User
from app.schemas import GuidelinesResponse, GuidelinesUpdateRequest
from app.services.guidelines_service import (
    get_or_create_guidelines_for_patient,
    update_guidelines_for_patient,
)

router = APIRouter()


def _to_guidelines_response(guidelines) -> GuidelinesResponse:
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


@router.get("/guidelines/{patient_id}", response_model=GuidelinesResponse)
async def get_guidelines(
    patient_id: str,
    current_user: User = Depends(require_role("therapist", "regular")),
    db: AsyncSession = Depends(get_db),
):
    guidelines = await get_or_create_guidelines_for_patient(
        patient_id, current_user, db
    )
    return _to_guidelines_response(guidelines)


@router.put("/guidelines/{patient_id}", response_model=GuidelinesResponse)
async def update_guidelines(
    patient_id: str,
    request: GuidelinesUpdateRequest,
    current_user: User = Depends(require_role("therapist", "regular")),
    db: AsyncSession = Depends(get_db),
):
    guidelines = await update_guidelines_for_patient(
        patient_id,
        response_tone=request.response_tone,
        coping_strategies=request.coping_strategies,
        behavioral_boundaries=request.behavioral_boundaries,
        sensitive_topics=request.sensitive_topics,
        current_user=current_user,
        db=db,
    )
    return _to_guidelines_response(guidelines)
