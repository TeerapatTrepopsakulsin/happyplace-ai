import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.main import app
from app.models.users import User
from app.models.chat_sessions import ChatSession
from app.models.messages import Message
from app.models.invitations import Invitation
from app.models.chatbot_guidelines import ChatbotGuidelines


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user-uuid"
    user.role = "regular"
    return user


@pytest.fixture
def mock_therapist():
    user = MagicMock()
    user.id = "therapist-uuid"
    user.role = "therapist"
    return user


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.id = "session-uuid"
    session.user_id = "user-uuid"
    session.title = "Test Session"
    session.created_at = datetime(2023, 1, 1)
    session.last_active = datetime(2023, 1, 1)
    return session


@pytest.fixture
def mock_message():
    message = MagicMock()
    message.id = "message-uuid"
    message.sender = "user"
    message.content = "Hello"
    message.emotion_label = None
    message.emotion_score = None
    message.danger_flag = False
    message.created_at = datetime(2023, 1, 1)
    return message


@pytest.mark.asyncio
async def test_get_sessions_success(mock_db, mock_redis, mock_user, mock_session):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db
    from app.core.redis import get_redis

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    # Mock query
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_session]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/chat/sessions")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "session-uuid"

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_session_success(mock_db, mock_redis, mock_user):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = mock_get_db

    # Mock session creation
    def set_session_attrs(session):
        session.id = "new-session-uuid"
        session.created_at = datetime(2023, 1, 1)
        session.title = "New conversation"

    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = set_session_attrs

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat/sessions")

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "new-session-uuid"

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_messages_success(mock_db, mock_redis, mock_user, mock_session, mock_message):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db
    from app.core.redis import get_redis

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    # Mock session and messages
    mock_db.get.return_value = mock_session
    mock_redis.get.return_value = None  # Cache miss
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_message]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/chat/sessions/session-uuid/messages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Hello"

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_messages_access_denied(mock_db, mock_redis, mock_user):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = mock_get_db

    # Mock session not belonging to user
    mock_other_session = MagicMock()
    mock_other_session.user_id = "other-user-uuid"
    mock_db.get.return_value = mock_other_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/chat/sessions/session-uuid/messages")

    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied"

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_send_message_success(mock_db, mock_redis, mock_user, mock_session):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db
    from app.core.redis import get_redis

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    # Mock session
    mock_db.get.return_value = mock_session
    mock_redis.get.return_value = None  # avoid AsyncMock from cache

    # Mock DB execute for history
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    # Mock message creation
    mock_user_msg = MagicMock()
    mock_user_msg.id = "user-msg-uuid"
    mock_user_msg.sender = "user"
    mock_user_msg.content = "Test message"
    mock_user_msg.emotion_label = None
    mock_user_msg.emotion_score = None
    mock_user_msg.danger_flag = False
    mock_user_msg.created_at = datetime(2023, 1, 1)

    mock_assistant_msg = MagicMock()
    mock_assistant_msg.id = "assistant-msg-uuid"
    mock_assistant_msg.sender = "assistant"
    mock_assistant_msg.content = "Response"
    mock_assistant_msg.emotion_label = None
    mock_assistant_msg.emotion_score = None
    mock_assistant_msg.danger_flag = False
    mock_assistant_msg.created_at = datetime(2023, 1, 1)

    mock_db.add.return_value = None
    mock_db.commit.return_value = None

    async def refresh_side_effect(obj):
        if obj.sender == "user":
            obj.created_at = datetime(2023, 1, 1)
            obj.id = "user-msg-uuid"
        elif obj.sender == "assistant":
            obj.created_at = datetime(2023, 1, 1)
            obj.id = "assistant-msg-uuid"

    mock_db.refresh.side_effect = refresh_side_effect

    with patch('app.api.chat.get_conversation_history', new_callable=AsyncMock, return_value=[]), \
         patch('app.api.chat.get_guidelines', new_callable=AsyncMock, return_value=None), \
         patch('app.api.chat.build_system_prompt', return_value="System prompt"), \
         patch('app.api.chat.call_groq', new_callable=AsyncMock, return_value="Response"), \
         patch('app.api.chat.update_session_cache', new_callable=AsyncMock), \
         patch('app.api.chat.publish_message_created'):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/sessions/session-uuid/messages",
                json={"content": "Test message"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_message"]["content"] == "Test message"
        assert data["assistant_message"]["content"] == "Response"

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_send_message_llm_failure(mock_db, mock_redis, mock_user, mock_session):
    from app.core.dependencies import get_current_user
    from app.db.session import get_db
    from app.core.redis import get_redis

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    mock_db.get.return_value = mock_session
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_redis.get.return_value = None

    # Mock DB execute for any calls
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    async def refresh_side_effect(obj):
        if obj.sender == "user":
            obj.created_at = datetime(2023, 1, 1)
            obj.id = "user-msg-uuid"

    mock_db.refresh.side_effect = refresh_side_effect

    with patch('app.api.chat.get_conversation_history', new_callable=AsyncMock, return_value=[]), \
         patch('app.api.chat.get_guidelines', new_callable=AsyncMock, return_value=None), \
         patch('app.api.chat.build_system_prompt', return_value="System prompt"), \
         patch('app.api.chat.call_groq', new_callable=AsyncMock, side_effect=Exception("LLM error")):

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/sessions/session-uuid/messages",
                json={"content": "Test message"}
            )

        assert response.status_code == 502
        assert response.json()["detail"] == "LLM service unavailable"

    app.dependency_overrides.clear()
    