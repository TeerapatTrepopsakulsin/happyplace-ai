from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, ARRAY
from sqlalchemy.sql import text

from app.models.base import Base


class ChatbotGuidelines(Base):
    __tablename__ = "chatbot_guidelines"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    authored_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    response_tone = Column(Text, nullable=True)
    coping_strategies = Column(Text, nullable=True)
    behavioral_boundaries = Column(Text, nullable=True)
    sensitive_topics = Column(ARRAY(Text), nullable=True)
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
