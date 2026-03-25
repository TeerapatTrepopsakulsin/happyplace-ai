import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.main import app
from app.models.users import User
from app.models.invitations import Invitation
from app.models.chat_sessions import ChatSession
from app.models.emotion_snapshots import EmotionSnapshot
from app.models.dashboard_summary import DashboardSummary
from app.models.danger_alerts import DangerAlert


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_therapist():
    user = MagicMock()
    user.id = "therapist-uuid"
    user.role = "therapist"
    return user


@pytest.fixture
def mock_guardian():
    user = MagicMock()
    user.id = "guardian-uuid"
    user.role = "guardian"
    return user


@pytest.fixture
def mock_patient():
    user = MagicMock()
    user.id = "patient-uuid"
    user.role = "regular"
    user.display_name = "Test Patient"
    return user


@pytest.fixture
def mock_invitation():
    invitation = MagicMock()
    invitation.sender_id = "patient-uuid"
    invitation.invitee_id = "therapist-uuid"
    return invitation


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.id = "session-uuid"
    session.user_id = "patient-uuid"
    session.last_active = datetime(2023, 1, 1)
    return session


@pytest.fixture
def mock_emotion_snapshot():
    snapshot = MagicMock()
    snapshot.session_id = "session-uuid"
    snapshot.dominant_emotion = "happy"
    snapshot.average_score = 0.8
    snapshot.snapshot_at = datetime(2023, 1, 1)
    return snapshot


@pytest.fixture
def mock_dashboard_summary():
    summary = MagicMock()
    summary.summary_date = datetime.utcnow().date()  # Make it recent
    summary.session_count = 2
    summary.total_messages = 10
    summary.avg_emotion_score = 0.7
    summary.dominant_emotion = "happy"
    summary.danger_event_count = 1
    return summary


@pytest.fixture
def mock_danger_alert():
    alert = MagicMock()
    alert.id = "alert-uuid"
    alert.user_id = "patient-uuid"
    alert.session_id = "session-uuid"
    alert.message_id = "message-uuid"
    alert.snippet = "Test snippet"
    alert.resolved = False
    alert.created_at = datetime(2023, 1, 1)
    return alert


@pytest.mark.asyncio
async def test_get_patients_success(mock_db, mock_therapist, mock_patient, mock_invitation, mock_session, mock_emotion_snapshot):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_therapist
    app.dependency_overrides[get_db] = mock_get_db

    # Mock invitation query
    mock_invitation_result = MagicMock()
    mock_invitation_result.fetchall.return_value = [("patient-uuid",)]
    mock_db.execute.return_value = mock_invitation_result

    # Mock patient query
    mock_patient_result = MagicMock()
    mock_patient_result.scalar_one_or_none.return_value = mock_patient
    mock_db.execute.side_effect = [mock_invitation_result, mock_patient_result]

    # Mock last_active query
    mock_last_active_result = MagicMock()
    mock_last_active_result.scalar.return_value = datetime(2023, 1, 1)
    mock_db.execute.side_effect = [mock_invitation_result, mock_patient_result, mock_last_active_result]

    # Mock emotion query
    mock_emotion_result = MagicMock()
    mock_emotion_result.scalar.return_value = "happy"
    mock_db.execute.side_effect = [mock_invitation_result, mock_patient_result, mock_last_active_result, mock_emotion_result]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/dashboard/patients")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == "patient-uuid"
    assert data[0]["display_name"] == "Test Patient"
    assert data[0]["latest_emotion"] == "happy"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_patient_summary_success(mock_db, mock_therapist, mock_invitation):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_therapist
    app.dependency_overrides[get_db] = mock_get_db

    # Mock invitation check
    mock_invitation_result = MagicMock()
    mock_invitation_result.scalar_one_or_none.return_value = mock_invitation
    mock_db.execute.return_value = mock_invitation_result

    # Mock summaries query - add two summaries: one recent, one previous
    mock_summary_recent = MagicMock()
    mock_summary_recent.summary_date = datetime.utcnow().date()
    mock_summary_recent.session_count = 2
    mock_summary_recent.total_messages = 10
    mock_summary_recent.avg_emotion_score = 0.7
    mock_summary_recent.dominant_emotion = "happy"
    mock_summary_recent.danger_event_count = 1

    mock_summary_previous = MagicMock()
    mock_summary_previous.summary_date = (datetime.utcnow() - timedelta(days=5)).date()
    mock_summary_previous.session_count = 1
    mock_summary_previous.total_messages = 5
    mock_summary_previous.avg_emotion_score = 0.65
    mock_summary_previous.dominant_emotion = "neutral"
    mock_summary_previous.danger_event_count = 0

    mock_summaries_result = MagicMock()
    mock_summaries_result.scalars.return_value.all.return_value = [mock_summary_recent, mock_summary_previous]
    mock_db.execute.side_effect = [mock_invitation_result, mock_summaries_result]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/dashboard/patients/patient-uuid/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["mood_trend"] == "stable"
    assert data["dominant_emotion_last_7d"] == "happy"
    assert data["session_count_last_7d"] == 3
    assert data["danger_events_last_7d"] == 1

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_alerts_success(mock_db, mock_therapist, mock_invitation, mock_danger_alert):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_therapist
    app.dependency_overrides[get_db] = mock_get_db

    # Mock patient ids
    mock_patient_result = MagicMock()
    mock_patient_result.fetchall.return_value = [("patient-uuid",)]
    mock_db.execute.return_value = mock_patient_result

    # Mock alerts query
    mock_alerts_result = MagicMock()
    mock_alerts_result.scalars.return_value.all.return_value = [mock_danger_alert]
    mock_db.execute.side_effect = [mock_patient_result, mock_alerts_result]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/dashboard/alerts")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == "patient-uuid"
    assert data[0]["snippet"] == "Test snippet"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_resolve_alert_success(mock_db, mock_therapist, mock_invitation, mock_danger_alert):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_therapist
    app.dependency_overrides[get_db] = mock_get_db

    # Mock alert query
    mock_alert_result = MagicMock()
    mock_alert_result.scalar_one_or_none.return_value = mock_danger_alert
    mock_db.execute.return_value = mock_alert_result

    # Mock invitation check
    mock_invitation_result = MagicMock()
    mock_invitation_result.scalar_one_or_none.return_value = mock_invitation
    mock_db.execute.side_effect = [mock_alert_result, mock_invitation_result]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/api/v1/dashboard/alerts/alert-uuid")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "alert-uuid"
    assert data["resolved"] is True

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_emotion_history_success(mock_db, mock_therapist, mock_invitation, mock_emotion_snapshot):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_therapist
    app.dependency_overrides[get_db] = mock_get_db

    # Mock invitation check
    mock_invitation_result = MagicMock()
    mock_invitation_result.scalar_one_or_none.return_value = mock_invitation
    mock_db.execute.return_value = mock_invitation_result

    # Mock emotion history query
    mock_history_result = MagicMock()
    mock_history_result.fetchall.return_value = [(datetime(2023, 1, 1), "happy", 0.8)]
    mock_db.execute.side_effect = [mock_invitation_result, mock_history_result]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/patients/patient-uuid/emotion-history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["dominant_emotion"] == "happy"
    assert data[0]["average_score"] == 0.8

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_progress_success(mock_db, mock_therapist, mock_invitation, mock_dashboard_summary):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_therapist
    app.dependency_overrides[get_db] = mock_get_db

    # Mock invitation check
    mock_invitation_result = MagicMock()
    mock_invitation_result.scalar_one_or_none.return_value = mock_invitation
    mock_db.execute.return_value = mock_invitation_result

    # Mock progress query
    mock_progress_result = MagicMock()
    mock_progress_result.scalars.return_value.all.return_value = [mock_dashboard_summary]
    mock_db.execute.side_effect = [mock_invitation_result, mock_progress_result]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/patients/patient-uuid/progress")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["session_count"] == 2
    assert data[0]["dominant_emotion"] == "happy"

    app.dependency_overrides.clear()