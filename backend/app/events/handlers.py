import logging
import os
from collections import Counter
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

# Import all models to ensure they are registered with SQLAlchemy
import app.models  # noqa: F401

from app.models.messages import Message
from app.models.emotion_snapshots import EmotionSnapshot
from app.models.dashboard_summary import DashboardSummary
from app.models.danger_alerts import DangerAlert
from app.services.emotion_service import analyse_emotion

logger = logging.getLogger(__name__)


async def _validate_payload(payload: dict, required_keys: list[str]) -> bool:
    return all(payload.get(k) for k in required_keys)


async def _load_message(db, message_id):
    stmt = select(Message).where(Message.id == message_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _compute_snapshot(session_messages):
    labels = [m.emotion_label for m in session_messages if m.emotion_label]
    scores = [m.emotion_score for m in session_messages if m.emotion_score is not None]
    dominant_emotion = Counter(labels).most_common(1)[0][0] if labels else None
    average_score = float(sum(scores) / len(scores)) if scores else None
    return dominant_emotion, average_score


def _compute_patient_stats(patient_all_today):
    total_messages = len(patient_all_today)
    scores_today = [
        m.emotion_score for m in patient_all_today if m.emotion_score is not None
    ]
    dominant_today_labels = [
        m.emotion_label for m in patient_all_today if m.emotion_label
    ]
    dominant_today = (
        Counter(dominant_today_labels).most_common(1)[0][0]
        if dominant_today_labels
        else None
    )
    avg_emotion_score = (
        float(sum(scores_today) / len(scores_today)) if scores_today else None
    )
    return total_messages, dominant_today, avg_emotion_score


async def handle_emotion(payload: dict, db):
    try:
        logger.info("handle_emotion received payload: %s", payload)

        if payload.get("sender") != "user":
            return

        if not await _validate_payload(
            payload, ["message_id", "content", "patient_id"]
        ):
            logger.warning("handle_emotion missing required payload fields")
            return

        message = await _load_message(db, payload["message_id"])
        if not message:
            logger.warning(
                "handle_emotion no message found for id: %s", payload["message_id"]
            )
            return

        emotion = await analyse_emotion(payload["content"])
        message.emotion_label = emotion.get("emotion_label", "neutral")
        message.emotion_score = emotion.get("emotion_score", 0.0)
        await db.commit()

        session_id = message.session_id
        session_messages = (
            (
                await db.execute(
                    select(Message).where(
                        Message.session_id == session_id, Message.sender == "user"
                    )
                )
            )
            .scalars()
            .all()
        )
        dominant_emotion, average_score = _compute_snapshot(session_messages)

        upsert_snapshot = (
            insert(EmotionSnapshot)
            .values(
                session_id=session_id,
                dominant_emotion=dominant_emotion,
                average_score=average_score,
                snapshot_at=func.now(),
            )
            .on_conflict_do_update(
                index_elements=[EmotionSnapshot.session_id],
                set_={
                    "dominant_emotion": dominant_emotion,
                    "average_score": average_score,
                    "snapshot_at": func.now(),
                },
            )
        )
        await db.execute(upsert_snapshot)

        today = date.today()
        today_msg_count = (
            await db.execute(
                select(func.count())
                .select_from(Message)
                .where(
                    Message.sender == "user",
                    Message.session_id == session_id,
                    func.date(Message.created_at) == today,
                )
            )
        ).scalar_one()
        session_count_delta = 1 if today_msg_count == 1 else 0

        patient_all_today = (
            (
                await db.execute(
                    select(Message).where(
                        Message.sender == "user",
                        func.date(Message.created_at) == today,
                    )
                )
            )
            .scalars()
            .all()
        )

        total_messages, dominant_today, avg_emotion_score = _compute_patient_stats(
            patient_all_today
        )

        upsert_summary = (
            insert(DashboardSummary)
            .values(
                user_id=payload["patient_id"],
                summary_date=today,
                session_count=session_count_delta,
                total_messages=total_messages,
                avg_emotion_score=avg_emotion_score,
                dominant_emotion=dominant_today,
                danger_event_count=0,
            )
            .on_conflict_do_update(
                index_elements=[
                    DashboardSummary.user_id,
                    DashboardSummary.summary_date,
                ],
                set_={
                    "session_count": DashboardSummary.session_count
                    + session_count_delta,
                    "total_messages": total_messages,
                    "avg_emotion_score": avg_emotion_score,
                    "dominant_emotion": dominant_today,
                },
            )
        )
        await db.execute(upsert_summary)
        await db.commit()

    except Exception:
        logger.exception("handle_emotion failed")


def _get_danger_keywords():
    danger_keywords = os.getenv("DANGER_KEYWORDS", "").split(",")
    return [k.strip().lower() for k in danger_keywords if k.strip()]


async def _load_message_by_id(db, message_id):
    msg_stmt = select(Message).where(Message.id == message_id)
    msg_result = await db.execute(msg_stmt)
    return msg_result.scalar_one_or_none()


async def _insert_danger_alert(db, patient_id, session_id, message_id, snippet):
    alert_values = {
        "user_id": patient_id,
        "session_id": session_id,
        "message_id": message_id,
        "snippet": snippet,
        "resolved": False,
    }
    ins_alert = insert(DangerAlert).values(**alert_values)
    await db.execute(ins_alert)


async def _increment_danger_summary(db, patient_id):
    today = date.today()
    upsert_summary = (
        insert(DashboardSummary)
        .values(
            user_id=patient_id,
            summary_date=today,
            session_count=0,
            total_messages=0,
            avg_emotion_score=None,
            dominant_emotion=None,
            danger_event_count=1,
        )
        .on_conflict_do_update(
            index_elements=[DashboardSummary.user_id, DashboardSummary.summary_date],
            set_={
                "danger_event_count": DashboardSummary.danger_event_count + 1,
            },
        )
    )
    await db.execute(upsert_summary)


async def handle_danger(payload: dict, db):
    try:
        logger.info("handle_danger received payload: %s", payload)

        if payload.get("sender") != "user":
            return

        if not await _validate_payload(
            payload, ["message_id", "session_id", "patient_id", "content"]
        ):
            logger.warning("handle_danger missing required payload fields")
            return

        danger_keywords = _get_danger_keywords()
        content_lower = payload["content"].lower()
        logger.info("Danger keywords configured: %s", danger_keywords)

        matched = [kw for kw in danger_keywords if kw in content_lower]
        logger.info("Danger keywords matched: %s", matched)

        if not matched:
            return

        msg = await _load_message_by_id(db, payload["message_id"])
        if msg is None:
            logger.warning(
                "handle_danger no message found for id: %s", payload["message_id"]
            )
            return

        msg.danger_flag = True
        await db.commit()

        await _insert_danger_alert(
            db,
            payload["patient_id"],
            payload["session_id"],
            payload["message_id"],
            payload["content"][:200],
        )
        await _increment_danger_summary(db, payload["patient_id"])
        await db.commit()

    except Exception:
        logger.exception("handle_danger failed")
