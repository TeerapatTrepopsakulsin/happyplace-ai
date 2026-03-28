import json
import logging
import os
from collections import Counter
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import SecretStr

from app.models.messages import Message
from app.models.emotion_snapshots import EmotionSnapshot
from app.models.dashboard_summary import DashboardSummary

logger = logging.getLogger(__name__)

VALID_EMOTION_LABELS = {"happy", "sad", "anxious", "angry", "neutral", "distressed"}


def _safe_emotion_result(raw_response: str):
    try:
        parsed = json.loads(raw_response)
        label = parsed.get("emotion_label", "neutral")
        score = parsed.get("emotion_score", 0.0)

        if not isinstance(label, str) or label.lower() not in VALID_EMOTION_LABELS:
            label = "neutral"

        try:
            score = float(score)
            if score < 0.0 or score > 1.0:
                score = 0.0
        except Exception:
            score = 0.0

        return {"emotion_label": label.lower(), "emotion_score": score}
    except Exception:
        logger.exception("Invalid emotion analysis response, returning default")
        return {"emotion_label": "neutral", "emotion_score": 0.0}


async def analyse_emotion(content: str) -> dict:
    if not isinstance(content, str) or content.strip() == "":
        return {"emotion_label": "neutral", "emotion_score": 0.0}

    model_name = os.getenv("GROQ_MODEL")
    api_key = os.getenv("GROQ_API_KEY")
    if not model_name or not api_key:
        logger.error("GROQ_MODEL or GROQ_API_KEY is not set")
        return {"emotion_label": "neutral", "emotion_score": 0.0}

    prompt = (
        """
Classify the emotion in the following text. Respond only with a JSON object with keys \"emotion_label\" and \"emotion_score\". No other text.

Text: %s
"""
        % content
    )

    try:
        llm = ChatGroq(model=model_name, api_key=SecretStr(api_key))
        response = await llm.ainvoke(
            [
                SystemMessage(content=prompt),
                HumanMessage(content=content),
            ]
        )
        return _safe_emotion_result(str(response.content))
    except Exception:
        logger.exception("Emotion analysis Groq call failed")
        return {"emotion_label": "neutral", "emotion_score": 0.0}


async def upsert_emotion_snapshot(session_id, db):
    stmt = select(Message).where(
        Message.session_id == session_id, Message.sender == "user"
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    if not rows:
        return

    labels = [m.emotion_label for m in rows if m.emotion_label]
    scores = [m.emotion_score for m in rows if m.emotion_score is not None]

    dominant_emotion = None
    if labels:
        dominant_emotion = Counter(labels).most_common(1)[0][0]

    average_score = None
    if scores:
        average_score = float(sum(scores)) / max(1, len(scores))

    upsert = (
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

    await db.execute(upsert)
    await db.commit()


async def upsert_dashboard_summary(patient_id, session_id, created_at, db):
    today = date.today()

    # User messages for today (all sessions)
    today_msg_stmt = select(Message).where(
        Message.sender == "user",
        func.date(Message.created_at) == today,
    )
    today_msg_result = await db.execute(today_msg_stmt)
    today_msgs = today_msg_result.scalars().all()

    total_messages = len(today_msgs)
    scores_today = [m.emotion_score for m in today_msgs if m.emotion_score is not None]
    dominant_today = None
    labels_today = [m.emotion_label for m in today_msgs if m.emotion_label]
    if labels_today:
        dominant_today = Counter(labels_today).most_common(1)[0][0]

    avg_emotion_score = (
        float(sum(scores_today) / len(scores_today)) if scores_today else None
    )

    # Determine first message in session today
    session_today_stmt = (
        select(func.count())
        .select_from(Message)
        .where(
            Message.sender == "user",
            Message.session_id == session_id,
            func.date(Message.created_at) == today,
        )
    )
    session_today_cnt = (await db.execute(session_today_stmt)).scalar_one() or 0
    session_count_delta = 1 if session_today_cnt == 1 else 0

    upsert = (
        insert(DashboardSummary)
        .values(
            user_id=patient_id,
            summary_date=today,
            session_count=session_count_delta,
            total_messages=total_messages,
            avg_emotion_score=avg_emotion_score,
            dominant_emotion=dominant_today,
        )
        .on_conflict_do_update(
            index_elements=[DashboardSummary.user_id, DashboardSummary.summary_date],
            set_={
                "session_count": DashboardSummary.session_count + session_count_delta,
                "total_messages": total_messages,
                "avg_emotion_score": avg_emotion_score,
                "dominant_emotion": dominant_today,
            },
        )
    )

    await db.execute(upsert)
    await db.commit()
