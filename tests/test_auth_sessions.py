import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from jose import jwt

from app.common.enums import UserRole
from app.core.config import settings
from app.core.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    ResourceNotFoundException,
)
from app.core.jwt_key_manager import JWTKeyManager
from app.core.security import create_access_token, create_refresh_token
from app.core.store import (
    decode_token,
    validate_token_payload,
    get_current_user,
    require_permission,
)
from app.platform.auth.model.user_session import UserSession
from app.platform.auth.repository.session_repository import SessionRepository
from app.platform.auth.service.auth_service import AuthService
from app.platform.users.model.user import User


# ==========================================
# 1. JWT Claims & Security Unit Tests
# ==========================================

@pytest.mark.asyncio
async def test_access_token_claims_and_sid(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    user = User(
        uuid=user_id,
        email="investor@example.com",
        role=UserRole.INVESTOR,
    )

    token = create_access_token(user, key_manager, session_id=session_id)
    payload = decode_token(token, key_manager)

    assert payload["sub"] == "investor@example.com"
    assert payload["user_id"] == str(user_id)
    assert payload["role"] == UserRole.INVESTOR.value
    assert payload["type"] == "access_token"
    assert payload["sid"] == str(session_id)
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload
    assert "wallet:read" in payload["permissions"]
    assert "project:request" in payload["permissions"]


@pytest.mark.asyncio
async def test_refresh_token_claims_and_no_permissions(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    user = User(
        uuid=user_id,
        email="investor@example.com",
        role=UserRole.INVESTOR,
    )

    token = create_refresh_token(user, key_manager, session_id=session_id)
    payload = decode_token(token, key_manager)

    assert payload["sub"] == "investor@example.com"
    assert payload["user_id"] == str(user_id)
    assert payload["sid"] == str(session_id)
    assert payload["type"] == "refresh_token"
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload
    # Assert permissions and role are NOT in refresh token
    assert "permissions" not in payload
    assert "role" not in payload


# ==========================================
# 2. Token Decoding & Validation Logic
# ==========================================

@pytest.mark.asyncio
async def test_token_validation_pipeline_success(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    user = User(uuid=user_id, email="admin@example.com", role=UserRole.ADMIN)

    token = create_access_token(user, key_manager, session_id=session_id)
    payload = validate_token_payload(token, "access_token", key_manager)

    assert payload["user_id"] == str(user_id)
    assert payload["sid"] == str(session_id)
    assert payload["type"] == "access_token"


@pytest.mark.asyncio
async def test_token_validation_pipeline_type_mismatch(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    user = User(uuid=user_id, email="admin@example.com", role=UserRole.ADMIN)

    # Generated access token passed to refresh validator
    token = create_access_token(user, key_manager, session_id=session_id)
    with pytest.raises(UnauthorizedException, match="Invalid token type"):
        validate_token_payload(token, "refresh_token", key_manager)


@pytest.mark.asyncio
async def test_token_validation_pipeline_missing_token(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    with pytest.raises(UnauthorizedException, match="Not authenticated"):
        validate_token_payload(None, "access_token", key_manager)


# ==========================================
# 3. Session Repository Tests
# ==========================================

def test_session_repository_crud():
    db = MagicMock()
    repo = SessionRepository(db)

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    now = datetime.utcnow()
    expires_at = now + timedelta(days=7)

    session_data = {
        "uuid": session_id,
        "user_id": user_id,
        "device_name": "MacBook Pro",
        "user_agent": "Mozilla/5.0",
        "ip_address": "127.0.0.1",
        "created_at": now,
        "last_seen": now,
        "expires_at": expires_at,
        "revoked": False,
        "revoked_at": None,
    }

    # Test create
    created = repo.create(session_data)
    assert db.add.called
    assert db.commit.called
    assert db.refresh.called

    # Test update_last_seen
    session_obj = UserSession(**session_data)
    repo.update_last_seen(session_obj)
    assert db.commit.called

    # Test revoke_session
    repo.revoke_session(session_obj)
    assert session_obj.revoked is True
    assert session_obj.revoked_at is not None


# ==========================================
# 4. Auth Service Session Flow Tests
# ==========================================

@pytest.mark.asyncio
async def test_create_session_and_tokens_on_login(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    user_service = MagicMock()
    session_repo = MagicMock()

    user_id = uuid.uuid4()
    user = User(
        uuid=user_id,
        email="testuser@example.com",
        name="Test User",
        role=UserRole.INVESTOR,
    )
    user_service.get_by_email.return_value = user

    def fake_create(data):
        return UserSession(**data)

    session_repo.create.side_effect = fake_create

    auth_service = AuthService(user_service, session_repo)
    result = auth_service.login_with_google(
        {"email": "testuser@example.com", "name": "Test User"},
        key_manager,
        client_info={"device_name": "iPhone", "user_agent": "Mobile Safari", "ip_address": "10.0.0.1"},
    )

    assert "access_token" in result
    assert "refresh_token" in result
    assert "session" in result

    session = result["session"]
    assert session.user_id == user_id
    assert session.device_name == "iPhone"
    assert session.revoked is False

    # Verify both tokens contain the session ID
    access_payload = decode_token(result["access_token"], key_manager)
    refresh_payload = decode_token(result["refresh_token"], key_manager)

    assert access_payload["sid"] == str(session.uuid)
    assert refresh_payload["sid"] == str(session.uuid)
    assert access_payload["user_id"] == str(user_id)
    assert refresh_payload["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_refresh_token_validates_active_session(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    user_service = MagicMock()
    session_repo = MagicMock()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    user = User(uuid=user_id, email="user@example.com", role=UserRole.INVESTOR, is_locked=False)
    user_service.repo.get_by_uuid.return_value = user

    active_session = UserSession(
        uuid=session_id,
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
        revoked_at=None,
    )
    session_repo.get_by_uuid.return_value = active_session

    auth_service = AuthService(user_service, session_repo)
    refresh_payload = {
        "user_id": str(user_id),
        "sid": str(session_id),
        "sub": "user@example.com",
        "type": "refresh_token",
    }

    result = auth_service.refresh_token(refresh_payload, key_manager)
    assert "access_token" in result
    assert "refresh_token" in result
    assert session_repo.update_last_seen.called

    # New tokens should keep the same sid
    new_access_payload = decode_token(result["access_token"], key_manager)
    assert new_access_payload["sid"] == str(session_id)


@pytest.mark.asyncio
async def test_refresh_token_fails_when_session_revoked(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    user_service = MagicMock()
    session_repo = MagicMock()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    revoked_session = UserSession(
        uuid=session_id,
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=True,
        revoked_at=datetime.utcnow(),
    )
    session_repo.get_by_uuid.return_value = revoked_session

    auth_service = AuthService(user_service, session_repo)
    refresh_payload = {
        "user_id": str(user_id),
        "sid": str(session_id),
        "sub": "user@example.com",
        "type": "refresh_token",
    }

    with pytest.raises(UnauthorizedException, match="Session has been revoked"):
        auth_service.refresh_token(refresh_payload, key_manager)


@pytest.mark.asyncio
async def test_refresh_token_fails_when_session_expired(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    user_service = MagicMock()
    session_repo = MagicMock()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    expired_session = UserSession(
        uuid=session_id,
        user_id=user_id,
        expires_at=datetime.utcnow() - timedelta(days=1),
        revoked=False,
        revoked_at=None,
    )
    session_repo.get_by_uuid.return_value = expired_session

    auth_service = AuthService(user_service, session_repo)
    refresh_payload = {
        "user_id": str(user_id),
        "sid": str(session_id),
        "sub": "user@example.com",
        "type": "refresh_token",
    }

    with pytest.raises(UnauthorizedException, match="Session has expired"):
        auth_service.refresh_token(refresh_payload, key_manager)


@pytest.mark.asyncio
async def test_refresh_token_fails_on_session_ownership_mismatch(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    user_service = MagicMock()
    session_repo = MagicMock()

    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    session_id = uuid.uuid4()

    # Session belongs to user_b
    session_belonging_to_b = UserSession(
        uuid=session_id,
        user_id=user_b,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
        revoked_at=None,
    )
    session_repo.get_by_uuid.return_value = session_belonging_to_b

    auth_service = AuthService(user_service, session_repo)
    refresh_payload = {
        "user_id": str(user_a),  # user_a trying to refresh user_b's session
        "sid": str(session_id),
        "sub": "usera@example.com",
        "type": "refresh_token",
    }

    with pytest.raises(UnauthorizedException, match="Invalid session ownership"):
        auth_service.refresh_token(refresh_payload, key_manager)


# ==========================================
# 5. Session Revocation & Permissions Tests
# ==========================================

def test_user_cannot_revoke_another_users_session():
    user_service = MagicMock()
    session_repo = MagicMock()

    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    session_id = uuid.uuid4()

    session_of_user_b = UserSession(
        uuid=session_id,
        user_id=user_b,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
    )
    session_repo.get_by_uuid.return_value = session_of_user_b

    auth_service = AuthService(user_service, session_repo)

    # user_a attempts to delete user_b's session
    with pytest.raises(ForbiddenException, match="Cannot revoke another user's session"):
        auth_service.revoke_session(user_id=user_a, session_id=session_id)


def test_user_can_revoke_own_session():
    user_service = MagicMock()
    session_repo = MagicMock()

    user_a = uuid.uuid4()
    session_id = uuid.uuid4()

    session_of_user_a = UserSession(
        uuid=session_id,
        user_id=user_a,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
    )
    session_repo.get_by_uuid.return_value = session_of_user_a

    auth_service = AuthService(user_service, session_repo)
    res = auth_service.revoke_session(user_id=user_a, session_id=session_id)

    assert session_repo.revoke_session.called
    assert res["message"] == "Session revoked successfully"


def test_revoke_all_sessions():
    user_service = MagicMock()
    session_repo = MagicMock()

    user_a = uuid.uuid4()
    auth_service = AuthService(user_service, session_repo)

    res = auth_service.revoke_all_sessions(user_id=user_a)
    session_repo.revoke_all_user_sessions.assert_called_once_with(user_a)
    assert res["message"] == "All sessions revoked successfully"


def test_require_permission_dependency_no_db():
    dependency = require_permission("wallet:read")
    payload_with_perm = {"permissions": ["wallet:read", "project:read"]}
    res = dependency(payload=payload_with_perm)
    assert res == payload_with_perm

    payload_without_perm = {"permissions": ["project:read"]}
    with pytest.raises(ForbiddenException, match="Permission denied"):
        dependency(payload=payload_without_perm)


def test_get_current_user_by_uuid():
    user_repo = MagicMock()
    user_id = uuid.uuid4()
    mock_user = User(uuid=user_id, email="test@example.com", role=UserRole.INVESTOR, is_locked=False)
    user_repo.get_by_uuid.return_value = mock_user

    payload = {"user_id": str(user_id), "sid": str(uuid.uuid4())}
    resolved_user = get_current_user(payload=payload, user_repo=user_repo)

    assert resolved_user == mock_user
    user_repo.get_by_uuid.assert_called_once_with(str(user_id))


def test_database_user_session_integration():
    from app.core.database import get_session_local
    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # Create a user in DB
        test_email = f"session_test_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            uuid=uuid.uuid4(),
            name="Session Test User",
            email=test_email,
            role=UserRole.INVESTOR.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        repo = SessionRepository(db)

        # 1. Create active session
        session_1 = repo.create({
            "uuid": uuid.uuid4(),
            "user_id": user.uuid,
            "device_name": "Test Laptop",
            "user_agent": "Pytest / 1.0",
            "ip_address": "192.168.1.50",
            "created_at": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "revoked": False,
            "revoked_at": None,
        })

        # 2. Create second session
        session_2 = repo.create({
            "uuid": uuid.uuid4(),
            "user_id": user.uuid,
            "device_name": "Test Phone",
            "user_agent": "Mobile Safari",
            "ip_address": "192.168.1.51",
            "created_at": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "revoked": False,
            "revoked_at": None,
        })

        # 3. List active sessions
        active = repo.get_active_sessions_by_user_id(user.uuid)
        assert len(active) == 2

        # 4. Revoke single session
        repo.revoke_session(session_1)
        active_after_one = repo.get_active_sessions_by_user_id(user.uuid)
        assert len(active_after_one) == 1
        assert active_after_one[0].uuid == session_2.uuid

        # 5. Revoke all sessions
        repo.revoke_all_user_sessions(user.uuid)
        active_after_all = repo.get_active_sessions_by_user_id(user.uuid)
        assert len(active_after_all) == 0

        # Cleanup
        db.query(UserSession).filter(UserSession.user_id == user.uuid).delete()
        db.delete(user)
        db.commit()

    finally:
        db.close()

