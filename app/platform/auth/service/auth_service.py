from app.core.security import create_access_token, create_refresh_token
from app.core.store import get_public_key
from app.platform.users.service.user_service import UserService
from jose.utils import base64url_encode
# تحويل المفتاح لـ JWK
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
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

    def refresh_token(self, payload):
        email = payload.email

        access_token = create_access_token({"sub": email})
        refresh_token = create_refresh_token({"sub": email})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def jwks(self):
        public_key = get_public_key()


        key = serialization.load_pem_public_key(public_key, backend=default_backend())
        numbers = key.public_numbers()

        e = base64url_encode(numbers.e.to_bytes(3, "big")).decode()
        n = base64url_encode(numbers.n.to_bytes(256, "big")).decode()

        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": "my-key-1",
                    "alg": "RS256",
                    "n": n,
                    "e": e,
                }
            ]
        }
