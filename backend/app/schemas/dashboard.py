from datetime import datetime
from pydantic import BaseModel


class PatientSummary(BaseModel):
    patient_id: str
    display_name: str | None
    last_active: str | None  # ISO format string or None
    latest_emotion: str | None


class DashboardSummaryResponse(BaseModel):
    mood_trend: str
    dominant_emotion_last_7d: str | None
    session_count_last_7d: int
    danger_events_last_7d: int


class AlertResponse(BaseModel):
    id: str
    patient_id: str
    session_id: str
    message_id: str
    snippet: str | None
    created_at: datetime


class AlertUpdateResponse(BaseModel):
    id: str
    resolved: bool


class EmotionHistoryResponse(BaseModel):
    snapshot_at: datetime
    dominant_emotion: str | None
    average_score: float | None


class ProgressResponse(BaseModel):
    summary_date: str  # date as string
    session_count: int
    total_messages: int
    avg_emotion_score: float | None
    dominant_emotion: str | None
    danger_event_count: int
