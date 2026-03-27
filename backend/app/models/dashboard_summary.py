from sqlalchemy import Column, ForeignKey, Integer, Float, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from app.models.base import Base


class DashboardSummary(Base):
    __tablename__ = "dashboard_summary"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    summary_date = Column(Date, nullable=False)
    session_count = Column(Integer, nullable=False, server_default=text("0"))
    total_messages = Column(Integer, nullable=False, server_default=text("0"))
    avg_session_duration_mins = Column(Float, nullable=True)
    avg_emotion_score = Column(Float, nullable=True)
    dominant_emotion = Column(Text, nullable=True)
    danger_event_count = Column(Integer, nullable=False, server_default=text("0"))
