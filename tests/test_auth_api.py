import uuid
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.common.enums import UserRole
from app.core.security import create_access_token, create_refresh_token
from app.core.jwt_key_manager import JWTKeyManager
from app.platform.users.model.user import User
from app.platform.auth.model.user_session import UserSession
from app.core.dependency_chain import get_auth_service, get_user_service, get_session_repo, get_user_repo
from app.core.store import get_jwt_key_manager


@pytest.mark.asyncio
async def test_api_session_endpoints(redis):
    key_manager = JWTKeyManager(redis)
    await key_manager.initialize()

    # Configure app state
    app.state.jwt_key_manager = key_manager

    client = TestClient(app)

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    other_session_id = uuid.uuid4()

    mock_user = User(
        uuid=user_id,
        email="test_investor@example.com",
        name="Test Investor",
        role=UserRole.INVESTOR,
        is_locked=False,
    )

    active_session_1 = UserSession(
        uuid=session_id,
        user_id=user_id,
        device_name="Mac",
        user_agent="Mozilla/5.0",
        ip_address="127.0.0.1",
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
        revoked_at=None,
    )

    active_session_2 = UserSession(
        uuid=other_session_id,
        user_id=user_id,
        device_name="iPhone",
        user_agent="Mobile Safari",
        ip_address="10.0.0.1",
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
        revoked_at=None,
    )

    # Generate tokens
    access_token = create_access_token(mock_user, key_manager, session_id=session_id)
    refresh_token = create_refresh_token(mock_user, key_manager, session_id=session_id)

    # Mock user repository get_by_uuid
    class MockUserRepo:
        def get_by_uuid(self, u_id):
            if str(u_id) == str(user_id):
                return mock_user
            return None

    class MockUserService:
        repo = MockUserRepo()
        def get_by_email(self, email):
            if email == mock_user.email:
                return mock_user
            return None

    class MockSessionRepo:
        def __init__(self):
            self.sessions = {
                str(session_id): active_session_1,
                str(other_session_id): active_session_2,
            }

        def get_by_uuid(self, s_id):
            return self.sessions.get(str(s_id))

        def get_active_sessions_by_user_id(self, u_id):
            return [s for s in self.sessions.values() if str(s.user_id) == str(u_id) and not s.revoked]

        def update_last_seen(self, s):
            s.last_seen = datetime.utcnow()
            return s

        def revoke_session(self, s):
            s.revoked = True
            s.revoked_at = datetime.utcnow()
            return s

        def revoke_all_user_sessions(self, u_id):
            count = 0
            for s in self.sessions.values():
                if str(s.user_id) == str(u_id) and not s.revoked:
                    s.revoked = True
                    s.revoked_at = datetime.utcnow()
                    count += 1
            return count

    mock_session_repo = MockSessionRepo()
    from app.platform.auth.service.auth_service import AuthService
    auth_service = AuthService(MockUserService(), mock_session_repo)

    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_user_service] = lambda: MockUserService()
    app.dependency_overrides[get_user_repo] = lambda: MockUserRepo()
    app.dependency_overrides[get_session_repo] = lambda: mock_session_repo
    app.dependency_overrides[get_jwt_key_manager] = lambda: key_manager

    try:
        # 1. GET /auth/me
        client.cookies.set("access_token", access_token)
        me_resp = client.get("/auth/me")
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["email"] == "test_investor@example.com"
        assert me_data["role"] == "investor"

        # 2. GET /auth/sessions
        sessions_resp = client.get("/auth/sessions")
        assert sessions_resp.status_code == 200
        sessions_data = sessions_resp.json()
        assert len(sessions_data) == 2
        # Check is_current flag on current session
        current_sessions = [s for s in sessions_data if s["uuid"] == str(session_id)]
        assert len(current_sessions) == 1
        assert current_sessions[0]["is_current"] is True

        other_sessions = [s for s in sessions_data if s["uuid"] == str(other_session_id)]
        assert len(other_sessions) == 1
        assert other_sessions[0]["is_current"] is False

        # 3. POST /auth/refresh
        client.cookies.set("refresh_token", refresh_token)
        refresh_resp = client.post("/auth/refresh")
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.cookies
        assert "refresh_token" in refresh_resp.cookies

        # 4. DELETE /auth/sessions/{other_session_id}
        del_one_resp = client.delete(f"/auth/sessions/{other_session_id}")
        assert del_one_resp.status_code == 200
        assert del_one_resp.json()["message"] == "Session revoked successfully"
        assert active_session_2.revoked is True

        # 5. Try to revoke another user's session
        alien_session_id = uuid.uuid4()
        alien_user_id = uuid.uuid4()
        mock_session_repo.sessions[str(alien_session_id)] = UserSession(
            uuid=alien_session_id,
            user_id=alien_user_id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked=False,
        )
        forbidden_resp = client.delete(f"/auth/sessions/{alien_session_id}")
        assert forbidden_resp.status_code == 403

        # 6. DELETE /auth/sessions (revoke all)
        del_all_resp = client.delete("/auth/sessions")
        assert del_all_resp.status_code == 200
        assert del_all_resp.json()["message"] == "All sessions revoked successfully"
        assert active_session_1.revoked is True

        # 7. POST /auth/logout
        logout_resp = client.post("/auth/logout")
        assert logout_resp.status_code == 200
        assert logout_resp.json()["message"] == "Logged out successfully"

        # 8. Unauthenticated requests to session endpoints
        client.cookies.clear()
        unauth_get = client.get("/auth/sessions")
        assert unauth_get.status_code == 401

        unauth_del = client.delete(f"/auth/sessions/{session_id}")
        assert unauth_del.status_code == 401

        unauth_del_all = client.delete("/auth/sessions")
        assert unauth_del_all.status_code == 401

        # 9. DELETE non-existent session
        client.cookies.set("access_token", access_token)
        non_existent_id = uuid.uuid4()
        not_found_resp = client.delete(f"/auth/sessions/{non_existent_id}")
        assert not_found_resp.status_code == 404

    finally:
        app.dependency_overrides.clear()
