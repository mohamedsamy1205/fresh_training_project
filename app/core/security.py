import uuid

from app.common.enums import UserRole
from app.platform.users.model.user import User
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

ROLE_PERMISSIONS = {
    UserRole.INVESTOR: [
        "wallet:read",
        "transaction:read",
        "project:read",
        "project:request",
    ],
    UserRole.ADMIN: [
        "wallet:read",
        "wallet:update",
        "mony:deposit",
        "mony:withdraw",
        "project:create",
        "project:close",
        "project:distribute_profits",
        "transaction:read",
        "transaction:create",
    ],
}
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user: User, key_manager):
    permissions = (
        ROLE_PERMISSIONS[UserRole.INVESTOR]
        if user.role == UserRole.INVESTOR
        else ROLE_PERMISSIONS[UserRole.ADMIN]
        if user.role == UserRole.ADMIN
        else []
    )
    payload = {
            "sub": user.email,
            "user_id": str(user.uuid),
            "role": user.role.value,
            "permissions": permissions,
            "jti": str(uuid.uuid4()),
        }
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "iat":  datetime.now(timezone.utc),"jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, key_manager.get_private_key(), algorithm=settings.ALGORITHM,
         headers={
            "kid": key_manager.get_kid(),
        },)

def create_refresh_token(data: dict, key_manager):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, key_manager.get_private_key(), algorithm=settings.ALGORITHM, 
        headers={
            "kid": key_manager.get_kid(),
        },)

