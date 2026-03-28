from sqlalchemy import Column, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DangerAlert(Base):
    __tablename__ = "danger_alerts"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    snippet = Column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
