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


def create_access_token(user: User, key_manager, session_id: str | uuid.UUID = None) -> str:
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    permissions = (
        ROLE_PERMISSIONS[UserRole.INVESTOR]
        if role_val == UserRole.INVESTOR.value
        else ROLE_PERMISSIONS[UserRole.ADMIN]
        if role_val == UserRole.ADMIN.value
        else []
    )
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    sid_val = str(session_id) if session_id else str(uuid.uuid4())

    payload = {
        "sub": user.email,
        "user_id": str(user.uuid),
        "role": role_val,
        "type": "access_token",
        "permissions": permissions,
        "sid": sid_val,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(
        payload,
        key_manager.get_private_key(),
        algorithm=settings.ALGORITHM,
        headers={
            "kid": key_manager.get_kid(),
        },
    )


def create_refresh_token(
    user_or_data: User | dict,
    key_manager,
    session_id: str | uuid.UUID = None
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    if isinstance(user_or_data, User):
        sid_val = str(session_id) if session_id else str(uuid.uuid4())
        payload = {
            "sub": user_or_data.email,
            "user_id": str(user_or_data.uuid),
            "sid": sid_val,
            "type": "refresh_token",
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": expire,
        }
    else:
        payload = user_or_data.copy()
        if "user_id" in payload and isinstance(payload["user_id"], uuid.UUID):
            payload["user_id"] = str(payload["user_id"])
        if session_id:
            payload["sid"] = str(session_id)
        elif "sid" not in payload:
            payload["sid"] = str(uuid.uuid4())
        if "jti" not in payload:
            payload["jti"] = str(uuid.uuid4())
        payload["type"] = "refresh_token"
        payload["iat"] = now
        payload["exp"] = expire

    # Do not put permissions or roles inside Refresh Token
    payload.pop("permissions", None)
    payload.pop("role", None)

    return jwt.encode(
        payload,
        key_manager.get_private_key(),
        algorithm=settings.ALGORITHM,
        headers={
            "kid": key_manager.get_kid(),
        },
    )


