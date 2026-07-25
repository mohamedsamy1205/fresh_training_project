from sqlalchemy.orm import Session
from app.features.users.models.user import User
from app.core.security import create_access_token
from app.core.security import create_refresh_token
from app.core.security import get_user
from app.features.users.repository.user_repository import UserRepository


class AuthService:

    @staticmethod
    def get_or_create_google_user(db: Session, user_info: dict):
        email = user_info.get("email")

        user = UserRepository.get_by_email(db, email)

        if user:
            return user

        # create new user
        new_user = UserRepository.create(db, {
            "name": user_info.get("name"),
            "email": email,
            "provider": "google",
            "hashed_password": None
        })

        return new_user

    @staticmethod
    def login_with_google(db: Session, user_info: dict):
        user = AuthService.get_or_create_google_user(db, user_info)

        access_token = create_access_token({
            "sub": user.email
        })
        refresh_token = create_refresh_token({
            "sub": user.email
        })
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_token(token: str):
        payload = get_user(token)
        user_id = payload.get("sub")

        new_access_token = create_access_token({"sub": user_id})

        return {"access_token": new_access_token}