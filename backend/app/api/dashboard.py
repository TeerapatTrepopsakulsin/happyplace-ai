from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.users import User
from app.schemas import (
    AlertResponse,
    AlertUpdateResponse,
    DashboardSummaryResponse,
    EmotionHistoryResponse,
    PatientSummary,
    ProgressResponse,
)
from app.services.dashboard_service import (
    list_alerts_for_therapist,
    list_emotion_history_for_user,
    list_patients_for_monitor,
    list_progress_for_user,
    get_patient_summary_for_monitor,
    resolve_alert_for_therapist,
)

router = APIRouter()


@router.get("/dashboard/patients", response_model=List[PatientSummary])
async def get_patients(
    current_user: User = Depends(require_role("therapist", "guardian")),
    db: AsyncSession = Depends(get_db),
):
    return [
        PatientSummary(**p) for p in await list_patients_for_monitor(current_user, db)
    ]


@router.get(
    "/dashboard/patients/{patient_id}/summary", response_model=DashboardSummaryResponse
)
async def get_patient_summary(
    patient_id: str,
    current_user: User = Depends(require_role("therapist", "guardian")),
    db: AsyncSession = Depends(get_db),
):
    summary = await get_patient_summary_for_monitor(patient_id, current_user, db)
    return DashboardSummaryResponse(**summary)


@router.get("/dashboard/alerts", response_model=List[AlertResponse])
async def get_alerts(
    current_user: User = Depends(require_role("therapist")),
    db: AsyncSession = Depends(get_db),
):
    return [
        AlertResponse(**a) for a in await list_alerts_for_therapist(current_user, db)
    ]


@router.patch("/dashboard/alerts/{alert_id}", response_model=AlertUpdateResponse)
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(require_role("therapist")),
    db: AsyncSession = Depends(get_db),
):
    alert = await resolve_alert_for_therapist(alert_id, current_user, db)
    return AlertUpdateResponse(**alert)


@router.get(
    "/patients/{patient_id}/emotion-history",
    response_model=List[EmotionHistoryResponse],
)
async def get_emotion_history(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_emotion_history_for_user(patient_id, current_user, db)
    return [EmotionHistoryResponse(**r) for r in rows]


@router.get("/patients/{patient_id}/progress", response_model=List[ProgressResponse])
async def get_progress(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_progress_for_user(patient_id, current_user, db)
    return [ProgressResponse(**r) for r in rows]
