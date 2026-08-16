from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.platform.auth.model.user_session import UserSession


class SessionRepository:
    def __init__(self, db: Session, redis=None):
        self.db = db
        self.redis = redis

    def create(self, session_data: dict) -> UserSession:
        session = UserSession(**session_data)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_uuid(self, session_uuid: UUID | str) -> Optional[UserSession]:
        if isinstance(session_uuid, str):
            try:
                session_uuid = UUID(session_uuid)
            except (ValueError, TypeError):
                return None
        return self.db.query(UserSession).filter(UserSession.uuid == session_uuid).first()

    def get_active_by_uuid(self, session_uuid: UUID | str) -> Optional[UserSession]:
        session = self.get_by_uuid(session_uuid)
        if not session:
            return None
        if session.revoked or (session.expires_at and session.expires_at < datetime.utcnow()):
            return None
        return session

    def get_active_sessions_by_user_id(self, user_uuid: UUID | str) -> List[UserSession]:
        if isinstance(user_uuid, str):
            try:
                user_uuid = UUID(user_uuid)
            except (ValueError, TypeError):
                return []
        now = datetime.utcnow()
        return (
            self.db.query(UserSession)
            .filter(
                UserSession.user_id == user_uuid,
                UserSession.revoked == False,
                UserSession.expires_at > now,
            )
            .order_by(UserSession.last_seen.desc())
            .all()
        )

    def get_all_sessions_by_user_id(self, user_uuid: UUID | str) -> List[UserSession]:
        if isinstance(user_uuid, str):
            try:
                user_uuid = UUID(user_uuid)
            except (ValueError, TypeError):
                return []
        return (
            self.db.query(UserSession)
            .filter(UserSession.user_id == user_uuid)
            .order_by(UserSession.created_at.desc())
            .all()
        )

    def update_last_seen(self, session: UserSession) -> UserSession:
        session.last_seen = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        return session

    def revoke_session(self, session: UserSession) -> UserSession:
        session.revoked = True
        session.revoked_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(session)
        return session

    def revoke_all_user_sessions(self, user_uuid: UUID | str) -> int:
        if isinstance(user_uuid, str):
            try:
                user_uuid = UUID(user_uuid)
            except (ValueError, TypeError):
                return 0
        now = datetime.utcnow()
        updated_count = (
            self.db.query(UserSession)
            .filter(
                UserSession.user_id == user_uuid,
                UserSession.revoked == False,
            )
            .update(
                {
                    UserSession.revoked: True,
                    UserSession.revoked_at: now,
                },
                synchronize_session=False,
            )
        )
        self.db.commit()
        return updated_count
