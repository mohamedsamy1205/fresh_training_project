import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    ResourceNotFoundException,
)
from app.core.security import create_access_token, create_refresh_token
from app.platform.auth.repository.session_repository import SessionRepository
from app.platform.users.model.user import User
from app.platform.users.service.user_service import UserService


class AuthService:
    def __init__(self, user_service: UserService, session_repo: SessionRepository):
        self.user_service = user_service
        self.session_repo = session_repo

    def get_or_create_google_user(self, user_info: dict) -> User:
        email = user_info.get("email")
        if not email:
            raise UnauthorizedException("Email is required from OAuth provider")

        user = self.user_service.get_by_email(email)
        if user:
            return user

        return self.user_service.create_google_user(
            name=user_info.get("name") or email.split("@")[0],
            email=email,
        )

    def create_session_and_tokens(
        self,
        user: User,
        key_manager,
        client_info: Optional[dict] = None
    ) -> dict:
        client_info = client_info or {}
        session_uuid = uuid.uuid4()
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

        session = self.session_repo.create({
            "uuid": session_uuid,
            "user_id": user.uuid,
            "device_name": client_info.get("device_name"),
            "user_agent": client_info.get("user_agent"),
            "ip_address": client_info.get("ip_address"),
            "created_at": now,
            "last_seen": now,
            "expires_at": expires_at,
            "revoked": False,
            "revoked_at": None,
        })

        access_token = create_access_token(user, key_manager, session_id=session.uuid)
        refresh_token = create_refresh_token(user, key_manager, session_id=session.uuid)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "session": session,
        }

    def login_with_google(
        self,
        user_info: dict,
        key_manager,
        client_info: Optional[dict] = None
    ) -> dict:
        user = self.get_or_create_google_user(user_info)
        return self.create_session_and_tokens(user, key_manager, client_info)

    def refresh_token(self, payload: dict, key_manager) -> dict:
        user_id = payload.get("user_id")
        sid = payload.get("sid")

        if not user_id or not sid:
            raise UnauthorizedException("Invalid token payload")

        session = self.session_repo.get_by_uuid(sid)
        if not session:
            raise UnauthorizedException("Session not found")

        if session.revoked or session.revoked_at is not None:
            raise UnauthorizedException("Session has been revoked")

        if session.expires_at and session.expires_at < datetime.utcnow():
            raise UnauthorizedException("Session has expired")

        if str(session.user_id) != str(user_id):
            raise UnauthorizedException("Invalid session ownership")

        user = self.user_service.repo.get_by_uuid(user_id)
        if not user:
            # Fallback to sub/email if uuid lookup returned None
            sub = payload.get("sub")
            if sub:
                user = self.user_service.get_by_email(sub)

        if not user:
            raise UnauthorizedException("User not found")

        if getattr(user, "is_locked", False):
            raise UnauthorizedException("User account is locked")

        # Update last_seen timestamp
        self.session_repo.update_last_seen(session)

        access_token = create_access_token(user, key_manager, session_id=session.uuid)
        refresh_token = create_refresh_token(user, key_manager, session_id=session.uuid)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def get_user_sessions(
        self,
        user_id: UUID | str,
        current_sid: Optional[UUID | str] = None
    ) -> List[dict]:
        sessions = self.session_repo.get_active_sessions_by_user_id(user_id)
        current_sid_str = str(current_sid) if current_sid else None

        result = []
        for s in sessions:
            result.append({
                "uuid": s.uuid,
                "device_name": s.device_name,
                "user_agent": s.user_agent,
                "ip_address": s.ip_address,
                "created_at": s.created_at,
                "last_seen": s.last_seen,
                "expires_at": s.expires_at,
                "revoked": s.revoked,
                "revoked_at": s.revoked_at,
                "is_current": (str(s.uuid) == current_sid_str) if current_sid_str else False,
            })
        return result

    def revoke_session(self, user_id: UUID | str, session_id: UUID | str) -> dict:
        session = self.session_repo.get_by_uuid(session_id)
        if not session:
            raise ResourceNotFoundException("Session not found")

        if str(session.user_id) != str(user_id):
            raise ForbiddenException("Cannot revoke another user's session")

        self.session_repo.revoke_session(session)
        return {"message": "Session revoked successfully"}

    def revoke_all_sessions(self, user_id: UUID | str) -> dict:
        self.session_repo.revoke_all_user_sessions(user_id)
        return {"message": "All sessions revoked successfully"}
