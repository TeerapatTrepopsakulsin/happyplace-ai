import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.events.handlers import handle_emotion, handle_danger


@pytest.mark.asyncio
async def test_handle_emotion_ignores_non_user_payload():
    db = AsyncMock()
    payload = {"sender": "assistant"}

    await handle_emotion(payload, db)

    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_handle_emotion_updates_message_and_summary(monkeypatch):
    message = MagicMock()
    message.id = "msg-uuid"
    message.session_id = "session-uuid"
    message.sender = "user"
    message.emotion_label = None
    message.emotion_score = None
    message.created_at = datetime.utcnow()

    select_message_result = MagicMock()
    select_message_result.scalar_one_or_none.return_value = message

    session_scalars = MagicMock()
    session_scalars.all.return_value = [message]
    session_messages_result = MagicMock()
    session_messages_result.scalars.return_value = session_scalars

    patient_scalars = MagicMock()
    patient_scalars.all.return_value = [message]
    patient_messages_result = MagicMock()
    patient_messages_result.scalars.return_value = patient_scalars

    db = AsyncMock()
    db.execute.side_effect = [select_message_result, session_messages_result, patient_messages_result]

    monkeypatch.setenv("GROQ_MODEL", "test-model")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    # stub emotion analysis to avoid external call
    with patch("app.events.handlers.analyse_emotion", new_callable=AsyncMock) as mock_analyse:
        mock_analyse.return_value = {"emotion_label": "happy", "emotion_score": 0.8}

        payload = {
            "sender": "user",
            "message_id": "msg-uuid",
            "session_id": "session-uuid",
            "patient_id": "patient-uuid",
            "content": "I am feeling good"
        }

        await handle_emotion(payload, db)

        assert message.emotion_label == "happy"
        assert message.emotion_score == 0.8
        assert db.commit.call_count >= 1


@pytest.mark.asyncio
async def test_handle_danger_matches_keyword_and_inserts_alert(monkeypatch):
    message = MagicMock()
    message.id = "msg-uuid"
    message.danger_flag = False

    select_message_result = MagicMock()
    select_message_result.scalar_one_or_none.return_value = message

    db = AsyncMock()
    db.execute.side_effect = [select_message_result, MagicMock(), MagicMock()]

    monkeypatch.setenv("DANGER_KEYWORDS", "hurt myself, suicide")

    payload = {
        "sender": "user",
        "message_id": "msg-uuid",
        "session_id": "session-uuid",
        "patient_id": "patient-uuid",
        "content": "I want to hurt myself"
    }

    await handle_danger(payload, db)

    assert message.danger_flag is True
    assert db.commit.call_count >= 1
    assert db.execute.call_count >= 3
