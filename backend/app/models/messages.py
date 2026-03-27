from sqlalchemy import Column, ForeignKey, Text, Float, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import text

from app.models.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )
    sender = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    emotion_label = Column(Text, nullable=True)
    emotion_score = Column(Float, nullable=True)
    danger_flag = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint("sender IN ('user', 'assistant')", name="chk_messages_sender"),
    )
