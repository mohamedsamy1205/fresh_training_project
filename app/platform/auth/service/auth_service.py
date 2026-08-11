from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, create_refresh_token
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
            email=email,
        )

    def login_with_google(self, user_info: dict, key_manager):
        user = self.get_or_create_google_user(user_info)

        access_token = create_access_token(user, key_manager)
        refresh_token = create_refresh_token({"sub": user.email}, key_manager)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_token(self, payload, key_manager):
        email = payload.email
        user = self.user_service.get_by_email(email)
        if not user: 
            raise UnauthorizedException("Not authenticated")

        access_token = create_access_token(user, key_manager)
        refresh_token = create_refresh_token({"sub": email}, key_manager)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
