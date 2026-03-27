from sqlalchemy import Column, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.sql import text

from app.models.base import Base


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    invitee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        CheckConstraint("sender_id != invitee_id", name="chk_invitations_sender_invitee_diff"),
        UniqueConstraint("sender_id", "invitee_id", name="uq_invitations_sender_invitee"),
    )
