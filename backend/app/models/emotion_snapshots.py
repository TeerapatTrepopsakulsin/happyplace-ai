from sqlalchemy import Column, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import text

from app.models.base import Base


class EmotionSnapshot(Base):
    __tablename__ = "emotion_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False, unique=True)
    dominant_emotion = Column(Text, nullable=True)
    average_score = Column(Float, nullable=True)
    snapshot_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
