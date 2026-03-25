import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.main import app
from app.models.users import User
from app.models.invitations import Invitation


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_patient():
    user = MagicMock()
    user.id = "patient-uuid"
    user.role = "regular"
    user.email = "patient@example.com"
    user.display_name = "Test Patient"
    return user


@pytest.fixture
def mock_therapist():
    user = MagicMock()
    user.id = "therapist-uuid"
    user.role = "therapist"
    user.email = "therapist@example.com"
    user.display_name = "Test Therapist"
    return user


@pytest.fixture
def mock_invitee():
    user = MagicMock()
    user.id = "invitee-uuid"
    user.role = "therapist"
    user.email = "invitee@example.com"
    user.display_name = "Invitee Therapist"
    return user


@pytest.fixture
def mock_invitation():
    invitation = MagicMock()
    invitation.id = "invitation-uuid"
    invitation.sender_id = "patient-uuid"
    invitation.invitee_id = "invitee-uuid"
    invitation.created_at = datetime(2023, 1, 1)
    return invitation


@pytest.mark.asyncio
async def test_create_invitation_success(mock_db, mock_patient, mock_invitee):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_patient
    app.dependency_overrides[get_db] = mock_get_db

    # Mock user lookup
    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = mock_invitee
    mock_db.execute.return_value = mock_user_result

    # Mock existing invitation check
    mock_existing_result = MagicMock()
    mock_existing_result.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [mock_user_result, mock_existing_result]

    # Mock commit and refresh
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    request_data = {"invitee_email": "invitee@example.com"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/invitations", json=request_data)

    assert response.status_code == 201
    data = response.json()
    assert data["invitee_email"] == "invitee@example.com"
    assert data["role_granted"] == "therapist"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_invitation_user_not_found(mock_db, mock_patient):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_patient
    app.dependency_overrides[get_db] = mock_get_db

    # Mock user lookup - not found
    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_user_result

    request_data = {"invitee_email": "nonexistent@example.com"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/invitations", json=request_data)

    assert response.status_code == 404
    data = response.json()
    assert "No user found with this email" in data["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_invitation_patient_role(mock_db, mock_patient):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_patient
    app.dependency_overrides[get_db] = mock_get_db

    # Mock user lookup - patient role
    mock_invitee_patient = MagicMock()
    mock_invitee_patient.role = "regular"
    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = mock_invitee_patient
    mock_db.execute.return_value = mock_user_result

    request_data = {"invitee_email": "patient@example.com"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/invitations", json=request_data)

    assert response.status_code == 400
    data = response.json()
    assert "Cannot invite a patient as a monitor" in data["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_invitation_already_exists(mock_db, mock_patient, mock_invitee, mock_invitation):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_patient
    app.dependency_overrides[get_db] = mock_get_db

    # Mock user lookup
    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = mock_invitee
    mock_db.execute.return_value = mock_user_result

    # Mock existing invitation check - exists
    mock_existing_result = MagicMock()
    mock_existing_result.scalar_one_or_none.return_value = mock_invitation
    mock_db.execute.side_effect = [mock_user_result, mock_existing_result]

    request_data = {"invitee_email": "invitee@example.com"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/invitations", json=request_data)

    assert response.status_code == 400
    data = response.json()
    assert "This user has already been invited" in data["detail"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_invitations_success(mock_db, mock_patient, mock_invitee, mock_invitation):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_patient
    app.dependency_overrides[get_db] = mock_get_db

    # Mock invitations query
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [(mock_invitation, mock_invitee)]
    mock_db.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/invitations")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["invitee_email"] == "invitee@example.com"
    assert data[0]["role_granted"] == "therapist"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_invitation_success(mock_db, mock_patient, mock_invitation):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_patient
    app.dependency_overrides[get_db] = mock_get_db

    # Mock invitation query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_invitation
    mock_db.execute.return_value = mock_result

    # Mock delete and commit
    mock_db.delete = MagicMock()
    mock_db.commit = AsyncMock()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete("/api/v1/invitations/invitation-uuid")

    assert response.status_code == 204

    app.dependency_overrides.clear()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_invitation_not_found(mock_db, mock_patient):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_patient
    app.dependency_overrides[get_db] = mock_get_db

    # Mock invitation query - not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete("/api/v1/invitations/invitation-uuid")

    assert response.status_code == 404
    data = response.json()
    assert "Invitation not found" in data["detail"]

    app.dependency_overrides.clear()