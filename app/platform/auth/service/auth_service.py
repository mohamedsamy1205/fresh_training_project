from app.platform.users.models.user import User
from app.core.security import create_access_token
from app.core.security import create_refresh_token
from app.core.security import get_user
from app.platform.users.service.user_service import UserService

class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    def get_or_create_google_user(self, user_info: dict):
        email = user_info.get("email")

        user = self.user_service.get_by_email(email)
        if user:
            return user

        return self.user_service.create_google_user(
            name=user_info.get("name"),
            email=email
        )

    def login_with_google(self, user_info: dict):
        user = self.get_or_create_google_user(user_info)

        access_token = create_access_token({"sub": user.email})
        refresh_token = create_refresh_token({"sub": user.email})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_token(self, token: str):
        payload = get_user(token)
        email = payload.get("sub")

        access_token = create_access_token({"sub": email})
        refresh_token = create_refresh_token({"sub": email})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
