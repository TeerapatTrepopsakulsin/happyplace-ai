import logging
import os
from collections import Counter
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from app.models.messages import Message
from app.models.emotion_snapshots import EmotionSnapshot
from app.models.dashboard_summary import DashboardSummary
from app.models.danger_alerts import DangerAlert
from app.services.emotion_service import analyse_emotion

logger = logging.getLogger(__name__)


async def handle_emotion(payload: dict, db):
    try:
        logger.info("handle_emotion received payload: %s", payload)

        if payload.get("sender") != "user":
            return

        message_id = payload.get("message_id")
        content = payload.get("content")
        patient_id = payload.get("patient_id")

        if not message_id or not content or not patient_id:
            logger.warning("handle_emotion missing required payload fields")
            return

        stmt = select(Message).where(Message.id == message_id)
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()
        if message is None:
            logger.warning("handle_emotion no message found for id: %s", message_id)
            return

        emotion = await analyse_emotion(content)
        message.emotion_label = emotion.get("emotion_label", "neutral")
        message.emotion_score = emotion.get("emotion_score", 0.0)

        await db.commit()

        # upsert emotion snapshot for the session
        session_id = message.session_id
        session_messages_stmt = select(Message).where(Message.session_id == session_id, Message.sender == "user")
        session_res = await db.execute(session_messages_stmt)
        session_messages = session_res.scalars().all()

        labels = [m.emotion_label for m in session_messages if m.emotion_label]
        scores = [m.emotion_score for m in session_messages if m.emotion_score is not None]
        dominant_emotion = Counter(labels).most_common(1)[0][0] if labels else None
        average_score = float(sum(scores) / len(scores)) if scores else None

        upsert_snapshot = insert(EmotionSnapshot).values(
            session_id=session_id,
            dominant_emotion=dominant_emotion,
            average_score=average_score,
            snapshot_at=func.now(),
        ).on_conflict_do_update(
            index_elements=[EmotionSnapshot.session_id],
            set_={
                "dominant_emotion": dominant_emotion,
                "average_score": average_score,
                "snapshot_at": func.now(),
            },
        )
        await db.execute(upsert_snapshot)

        # dashboard summary upsert for today
        today = date.today()
        today_messages_stmt = select(Message).where(
            Message.sender == "user",
            Message.session_id == session_id,
            func.date(Message.created_at) == today,
        )
        today_msg_count = (await db.execute(select(func.count()).select_from(Message).where(
            Message.sender == "user",
            Message.session_id == session_id,
            func.date(Message.created_at) == today,
        ))).scalar_one()
        session_count_delta = 1 if today_msg_count == 1 else 0

        patient_today_stmt = select(Message).where(
            Message.sender == "user",
            Message.session_id == session_id,
            func.date(Message.created_at) == today,
        )
        # It is possible messages from other sessions should be included; find all patient user messages for today
        patient_all_today_stmt = select(Message).where(
            Message.sender == "user",
            func.date(Message.created_at) == today,
        )
        patient_all_today = (await db.execute(patient_all_today_stmt)).scalars().all()

        total_messages = len(patient_all_today)
        scores_today = [m.emotion_score for m in patient_all_today if m.emotion_score is not None]
        dominant_today_labels = [m.emotion_label for m in patient_all_today if m.emotion_label]
        dominant_today = Counter(dominant_today_labels).most_common(1)[0][0] if dominant_today_labels else None
        avg_emotion_score = float(sum(scores_today)/len(scores_today)) if scores_today else None

        upsert_summary = insert(DashboardSummary).values(
            user_id=patient_id,
            summary_date=today,
            session_count=session_count_delta,
            total_messages=total_messages,
            avg_emotion_score=avg_emotion_score,
            dominant_emotion=dominant_today,
            danger_event_count=0,
        ).on_conflict_do_update(
            index_elements=[DashboardSummary.user_id, DashboardSummary.summary_date],
            set_={
                "session_count": DashboardSummary.session_count + session_count_delta,
                "total_messages": total_messages,
                "avg_emotion_score": avg_emotion_score,
                "dominant_emotion": dominant_today,
            },
        )
        await db.execute(upsert_summary)
        await db.commit()

    except Exception:
        logger.exception("handle_emotion failed")


async def handle_danger(payload: dict, db):
    try:
        logger.info("handle_danger received payload: %s", payload)

        if payload.get("sender") != "user":
            return

        message_id = payload.get("message_id")
        session_id = payload.get("session_id")
        patient_id = payload.get("patient_id")
        content = payload.get("content")

        if not message_id or not session_id or not patient_id or not content:
            logger.warning("handle_danger missing required payload fields")
            return

        danger_keywords = os.getenv("DANGER_KEYWORDS", "").split(",")
        danger_keywords = [k.strip().lower() for k in danger_keywords if k.strip()]

        content_lower = content.lower()
        matched = any(kw in content_lower for kw in danger_keywords)
        if not matched:
            return

        msg_stmt = select(Message).where(Message.id == message_id)
        msg_result = await db.execute(msg_stmt)
        msg = msg_result.scalar_one_or_none()
        if msg is None:
            logger.warning("handle_danger no message found for id: %s", message_id)
            return

        msg.danger_flag = True
        await db.commit()

        # insert danger alert
        alert_values = {
            "user_id": patient_id,
            "session_id": session_id,
            "message_id": message_id,
            "snippet": content[:200],
            "resolved": False,
        }
        ins_alert = insert(DangerAlert).values(**alert_values)
        await db.execute(ins_alert)

        # increment danger counter in dashboard summary
        today = date.today()
        upsert_summary = insert(DashboardSummary).values(
            user_id=patient_id,
            summary_date=today,
            session_count=0,
            total_messages=0,
            avg_emotion_score=None,
            dominant_emotion=None,
            danger_event_count=1,
        ).on_conflict_do_update(
            index_elements=[DashboardSummary.user_id, DashboardSummary.summary_date],
            set_={
                "danger_event_count": DashboardSummary.danger_event_count + 1,
            },
        )
        await db.execute(upsert_summary)
        await db.commit()

    except Exception:
        logger.exception("handle_danger failed")
