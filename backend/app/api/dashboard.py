from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from collections import Counter
from datetime import datetime, timedelta

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.users import User
from app.models.invitations import Invitation
from app.models.chat_sessions import ChatSession
from app.models.emotion_snapshots import EmotionSnapshot
from app.models.dashboard_summary import DashboardSummary
from app.models.danger_alerts import DangerAlert
from app.schemas import (
    AlertResponse,
    AlertUpdateResponse,
    DashboardSummaryResponse,
    EmotionHistoryResponse,
    PatientSummary,
    ProgressResponse,
)

router = APIRouter()


@router.get("/dashboard/patients", response_model=List[PatientSummary])
async def get_patients(
    current_user: User = Depends(require_role("therapist", "guardian")),
    db: AsyncSession = Depends(get_db),
):
    # Get patients who invited current user
    stmt = select(Invitation.sender_id).where(Invitation.invitee_id == current_user.id)
    result = await db.execute(stmt)
    patient_ids = [row[0] for row in result.fetchall()]

    if not patient_ids:
        return []

    patients = []
    for patient_id in patient_ids:
        # Get patient info
        patient_stmt = select(User).where(User.id == patient_id)
        patient_result = await db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()
        if not patient:
            continue

        # Get latest last_active
        last_active_stmt = select(func.max(ChatSession.last_active)).where(
            ChatSession.user_id == patient_id
        )
        last_active_result = await db.execute(last_active_stmt)
        last_active = last_active_result.scalar()

        # Get latest emotion
        emotion_stmt = (
            select(EmotionSnapshot.dominant_emotion)
            .join(ChatSession, EmotionSnapshot.session_id == ChatSession.id)
            .where(ChatSession.user_id == patient_id)
            .order_by(desc(EmotionSnapshot.snapshot_at))
            .limit(1)
        )
        emotion_result = await db.execute(emotion_stmt)
        latest_emotion = emotion_result.scalar()

        patients.append(
            PatientSummary(
                patient_id=str(patient_id),
                display_name=str(patient.display_name)
                if patient.display_name
                else None,
                last_active=last_active.isoformat() if last_active else None,
                latest_emotion=latest_emotion,
            )
        )

    return patients


async def _verify_invitation(patient_id: str, current_user: User, db: AsyncSession):
    invitation_stmt = select(Invitation).where(
        and_(
            Invitation.sender_id == patient_id, Invitation.invitee_id == current_user.id
        )
    )
    invitation_result = await db.execute(invitation_stmt)
    invitation = invitation_result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=403, detail="Access denied")


def _calculate_mood_trend(summaries: List[DashboardSummary]) -> str:
    if not summaries:
        return "stable"

    now_date = datetime.utcnow().date()
    recent_cutoff = now_date - timedelta(days=3)

    recent_summaries = [s for s in summaries if s.summary_date >= recent_cutoff]
    previous_summaries = [s for s in summaries if s.summary_date < recent_cutoff]

    def avg_score(items):
        scores = [s.avg_emotion_score for s in items if s.avg_emotion_score is not None]
        return sum(scores) / len(scores) if scores else 0

    recent_avg = avg_score(recent_summaries)
    previous_avg = avg_score(previous_summaries)

    if recent_avg > previous_avg + 0.05:
        return "improving"
    if recent_avg < previous_avg - 0.05:
        return "declining"
    return "stable"


def _get_dominant_emotion(summaries: list[DashboardSummary]) -> str | None:
    emotions = [s.dominant_emotion for s in summaries if s.dominant_emotion]
    if not emotions:
        return None

    emotion_counts = Counter(emotions)
    max_count = max(emotion_counts.values())
    candidates = [str(e) for e, count in emotion_counts.items() if count == max_count]

    if len(candidates) == 1:
        return candidates[0]

    return _resolve_emotion_tie(summaries, candidates)


def _resolve_emotion_tie(
    summaries: list[DashboardSummary], candidates: list[str]
) -> str | None:
    sorted_summaries = sorted(summaries, key=lambda s: s.summary_date, reverse=True)
    for summary in sorted_summaries:
        if summary.dominant_emotion in candidates:
            return str(summary.dominant_emotion)
    return None


def _build_empty_summary_response() -> DashboardSummaryResponse:
    return DashboardSummaryResponse(
        mood_trend="stable",
        dominant_emotion_last_7d=None,
        session_count_last_7d=0,
        danger_events_last_7d=0,
    )


async def _fetch_recent_summaries(
    patient_id: str, db: AsyncSession
) -> list[DashboardSummary]:
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    stmt = (
        select(DashboardSummary)
        .where(
            and_(
                DashboardSummary.user_id == patient_id,
                DashboardSummary.summary_date >= seven_days_ago.date(),
            )
        )
        .order_by(DashboardSummary.summary_date)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/dashboard/patients/{patient_id}/summary", response_model=DashboardSummaryResponse
)
async def get_patient_summary(
    patient_id: str,
    current_user: User = Depends(require_role("therapist", "guardian")),
    db: AsyncSession = Depends(get_db),
):
    await _verify_invitation(patient_id, current_user, db)

    summaries = await _fetch_recent_summaries(patient_id, db)
    if not summaries:
        return _build_empty_summary_response()

    return DashboardSummaryResponse(
        mood_trend=_calculate_mood_trend(summaries),
        dominant_emotion_last_7d=_get_dominant_emotion(summaries),
        session_count_last_7d=int(sum(s.session_count for s in summaries)),
        danger_events_last_7d=int(sum(s.danger_event_count for s in summaries)),
    )


@router.get("/dashboard/alerts", response_model=List[AlertResponse])
async def get_alerts(
    current_user: User = Depends(require_role("therapist")),
    db: AsyncSession = Depends(get_db),
):
    # Get patients who invited current user
    stmt = select(Invitation.sender_id).where(Invitation.invitee_id == current_user.id)
    result = await db.execute(stmt)
    patient_ids = [row[0] for row in result.fetchall()]

    if not patient_ids:
        return []

    # Get unresolved alerts for these patients
    alerts_stmt = (
        select(DangerAlert)
        .where(and_(DangerAlert.user_id.in_(patient_ids), ~DangerAlert.resolved))
        .order_by(desc(DangerAlert.created_at))
    )
    alerts_result = await db.execute(alerts_stmt)
    alerts = alerts_result.scalars().all()

    return [
        AlertResponse(
            id=str(alert.id),
            patient_id=str(alert.user_id),
            session_id=str(alert.session_id),
            message_id=str(alert.message_id),
            snippet=str(alert.snippet) if alert.snippet else None,
            created_at=datetime.fromtimestamp(alert.created_at.timestamp()),
        )
        for alert in alerts
    ]


@router.patch("/dashboard/alerts/{alert_id}", response_model=AlertUpdateResponse)
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(require_role("therapist")),
    db: AsyncSession = Depends(get_db),
):
    # Get the alert
    alert_stmt = select(DangerAlert).where(DangerAlert.id == alert_id)
    alert_result = await db.execute(alert_stmt)
    alert = alert_result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Verify the alert belongs to a patient who invited this therapist
    invitation_stmt = select(Invitation).where(
        and_(
            Invitation.sender_id == alert.user_id,
            Invitation.invitee_id == current_user.id,
        )
    )
    invitation_result = await db.execute(invitation_stmt)
    invitation = invitation_result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=403, detail="Access denied")

    # Mark as resolved
    alert.resolved = True
    await db.commit()

    return AlertUpdateResponse(id=alert_id, resolved=True)


@router.get(
    "/patients/{patient_id}/emotion-history",
    response_model=List[EmotionHistoryResponse],
)
async def get_emotion_history(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check access
    if current_user.role == "regular" and str(current_user.id) != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role in ["therapist", "guardian"]:
        # Verify invitation
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

    # Get emotion history
    stmt = (
        select(
            EmotionSnapshot.snapshot_at,
            EmotionSnapshot.dominant_emotion,
            EmotionSnapshot.average_score,
        )
        .join(ChatSession, EmotionSnapshot.session_id == ChatSession.id)
        .where(ChatSession.user_id == patient_id)
        .order_by(EmotionSnapshot.snapshot_at)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    return [
        EmotionHistoryResponse(
            snapshot_at=row[0], dominant_emotion=row[1], average_score=row[2]
        )
        for row in rows
    ]


@router.get("/patients/{patient_id}/progress", response_model=List[ProgressResponse])
async def get_progress(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check access (same as above)
    if current_user.role == "regular" and str(current_user.id) != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role in ["therapist", "guardian"]:
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

    # Get progress
    stmt = (
        select(DashboardSummary)
        .where(DashboardSummary.user_id == patient_id)
        .order_by(DashboardSummary.summary_date)
    )
    result = await db.execute(stmt)
    summaries = result.scalars().all()

    return [
        ProgressResponse(
            summary_date=str(s.summary_date),
            session_count=int(s.session_count),
            total_messages=int(s.total_messages),
            avg_emotion_score=float(s.avg_emotion_score)
            if s.avg_emotion_score is not None
            else None,
            dominant_emotion=str(s.dominant_emotion) if s.dominant_emotion else None,
            danger_event_count=int(s.danger_event_count),
        )
        for s in summaries
    ]
