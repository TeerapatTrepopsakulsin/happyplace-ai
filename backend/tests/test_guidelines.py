import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.main import app
from app.models.users import User
from app.models.invitations import Invitation
from app.models.chatbot_guidelines import ChatbotGuidelines


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
def mock_invitation():
    invitation = MagicMock()
    invitation.sender_id = "patient-uuid"
    invitation.invitee_id = "therapist-uuid"
    return invitation


@pytest.fixture
def mock_guidelines():
    guidelines = MagicMock()
    guidelines.id = "guidelines-uuid"
    guidelines.user_id = "patient-uuid"
    guidelines.authored_by = "therapist-uuid"
    guidelines.response_tone = "calm"
    guidelines.coping_strategies = "Deep breathing"
    guidelines.behavioral_boundaries = "No self-harm"
    guidelines.sensitive_topics = ["suicide", "violence"]
    guidelines.updated_at = datetime(2023, 1, 1)
    return guidelines


@pytest.mark.asyncio
async def test_get_guidelines_success(mock_db, mock_therapist, mock_invitation, mock_guidelines):
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

    # Mock guidelines query
    mock_guidelines_result = MagicMock()
    mock_guidelines_result.scalar_one_or_none.return_value = mock_guidelines
    mock_db.execute.side_effect = [mock_invitation_result, mock_guidelines_result]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/guidelines/patient-uuid")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "guidelines-uuid"
    assert data["response_tone"] == "calm"
    assert data["sensitive_topics"] == ["suicide", "violence"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_guidelines_not_found(mock_db, mock_therapist, mock_invitation):
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

    # Mock guidelines query - not found
    mock_guidelines_result = MagicMock()
    mock_guidelines_result.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [mock_invitation_result, mock_guidelines_result]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/guidelines/patient-uuid")

    assert response.status_code == 404
    data = response.json()
    assert "Guidelines not found" in data["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_guidelines_success(mock_db, mock_therapist, mock_invitation, mock_guidelines):
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

    # Mock upsert and fetch
    mock_upsert_result = MagicMock()
    mock_db.execute.side_effect = [mock_invitation_result, mock_upsert_result, mock_upsert_result]

    mock_fetch_result = MagicMock()
    mock_fetch_result.scalar_one.return_value = mock_guidelines
    mock_db.execute.side_effect = [mock_invitation_result, mock_upsert_result, mock_fetch_result]

    request_data = {
        "response_tone": "supportive",
        "coping_strategies": "Mindfulness",
        "behavioral_boundaries": "Stay safe",
        "sensitive_topics": ["depression"]
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put("/api/v1/guidelines/patient-uuid", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["response_tone"] == "calm"  # from mock

    app.dependency_overrides.clear()