from sqlalchemy import and_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chatbot_guidelines import ChatbotGuidelines
from app.models.invitations import Invitation
from app.models.users import User
from app.services.errors import ForbiddenError


async def _verify_guideline_access(
    patient_id: str, current_user: User, db: AsyncSession
) -> None:
    if current_user.role == "regular":
        if str(current_user.id) != patient_id:
            raise ForbiddenError("Access denied")
        return

    invitation_stmt = select(Invitation).where(
        and_(
            Invitation.sender_id == patient_id,
            Invitation.invitee_id == current_user.id,
        )
    )
    invitation_result = await db.execute(invitation_stmt)
    invitation = invitation_result.scalar_one_or_none()
    if not invitation:
        raise ForbiddenError("Access denied")


async def get_or_create_guidelines_for_patient(
    patient_id: str, current_user: User, db: AsyncSession
) -> ChatbotGuidelines:
    await _verify_guideline_access(patient_id, current_user, db)

    stmt = select(ChatbotGuidelines).where(ChatbotGuidelines.user_id == patient_id)
    result = await db.execute(stmt)
    guidelines = result.scalar_one_or_none()
    if not guidelines:
        guidelines = ChatbotGuidelines(
            user_id=patient_id,
            authored_by=current_user.id,
            response_tone=None,
            coping_strategies=None,
            behavioral_boundaries=None,
            sensitive_topics=[],
        )
        db.add(guidelines)
        await db.commit()
        await db.refresh(guidelines)

    return guidelines


async def update_guidelines_for_patient(
    patient_id: str,
    *,
    response_tone: str | None,
    coping_strategies: str | None,
    behavioral_boundaries: str | None,
    sensitive_topics: list[str] | None,
    current_user: User,
    db: AsyncSession,
) -> ChatbotGuidelines:
    await _verify_guideline_access(patient_id, current_user, db)

    insert_stmt = insert(ChatbotGuidelines).values(
        user_id=patient_id,
        authored_by=str(current_user.id),
        response_tone=response_tone,
        coping_strategies=coping_strategies,
        behavioral_boundaries=behavioral_boundaries,
        sensitive_topics=sensitive_topics,
    )
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["user_id"],
        set_={
            "authored_by": str(current_user.id),
            "response_tone": response_tone,
            "coping_strategies": coping_strategies,
            "behavioral_boundaries": behavioral_boundaries,
            "sensitive_topics": sensitive_topics,
            "updated_at": text("now()"),
        },
    )
    await db.execute(upsert_stmt)
    await db.commit()

    stmt = select(ChatbotGuidelines).where(ChatbotGuidelines.user_id == patient_id)
    result = await db.execute(stmt)
    return result.scalar_one()
