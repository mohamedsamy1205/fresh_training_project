from uuid import UUID
from typing import Optional
from app.platform.users.model.user import User


class UserRepository:
    def __init__(self, db, redis=None):
        self.db = db
        self.redis = redis

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db.query(User).filter(User.uuid == user_id).first()

    def get_by_uuid(self, user_uuid: UUID | str) -> Optional[User]:
        if isinstance(user_uuid, str):
            try:
                user_uuid = UUID(user_uuid)
            except (ValueError, TypeError):
                return None
        return self.db.query(User).filter(User.uuid == user_uuid).first()

    def get_users(self, limit, skip, sort_by, order):
        query = self.db.query(User)

        sort_column = getattr(User, sort_by, None)
        if sort_column is not None:
            if order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        return query.offset(skip).limit(limit).all()

    def create(self, user_data: dict):
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, updates: dict):
        for key, value in updates.items():
            setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User):
        self.db.delete(user)