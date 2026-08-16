from typing import Optional
from uuid import UUID
from fastapi import Request, Depends, Path
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException, ForbiddenException, ResourceNotFoundException
from app.core.redis import get_redis
from app.common.enums import UserRole
from app.platform.users.model.user import User
from app.platform.users.repository.user_repository import UserRepository
from app.platform.auth.repository.session_repository import SessionRepository


def get_jwt_key_manager(request: Request):
    return request.app.state.jwt_key_manager


from app.core.dependency_chain import get_user_repo, get_session_repo


def get_public_key():
    with open(settings.PUBLIC_KEY_PATH, "r") as f:
        public_key = f.read()
    if isinstance(public_key, str):
        public_key = public_key.encode()
    return public_key


def decode_token(token: str, key_manager) -> dict:
    """
    Decode and verify JWT signature and expiration using the active RSA public key.
    """
    try:
        payload = jwt.decode(
            token,
            key_manager.get_public_key(),
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        raise UnauthorizedException("Invalid or expired token")


def validate_token_payload(token: Optional[str], expected_type: str, key_manager) -> dict:
    """
    Reusable validation pipeline:
    1. Extract token presence
    2. Decode token signature and expiration
    3. Validate token type
    4. Extract and validate required claims
    """
    if not token:
        raise UnauthorizedException("Not authenticated")

    payload = decode_token(token, key_manager)

    if payload.get("type") != expected_type:
        raise UnauthorizedException("Invalid token type")

    if not payload.get("user_id"):
        raise UnauthorizedException("Invalid token payload")

    return payload


def get_access_payload(
    request: Request,
    key_manager=Depends(get_jwt_key_manager),
) -> dict:
    """
    Dependency returning the Access Token payload claims without querying the database.
    """
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    return validate_token_payload(token, "access_token", key_manager)


def get_refresh_payload(
    request: Request,
    key_manager=Depends(get_jwt_key_manager),
) -> dict:
    """
    Dependency returning the Refresh Token payload claims without querying the database.
    """
    token = request.cookies.get("refresh_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    return validate_token_payload(token, "refresh_token", key_manager)


def get_current_user(
    payload: dict = Depends(get_access_payload),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """
    Dependency resolving the authenticated database User using the JWT user_id claim (UUID).
    """
    user_id = payload.get("user_id")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    user = user_repo.get_by_uuid(user_id)
    if not user:
        raise UnauthorizedException("User not found")

    if getattr(user, "is_locked", False):
        raise ForbiddenException("User account is locked")

    return user


def get_user_from_refrsh_token(
    payload: dict = Depends(get_refresh_payload),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """
    Helper dependency resolving the database User from the refresh token payload.
    """
    user_id = payload.get("user_id")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    user = user_repo.get_by_uuid(user_id)
    if not user:
        raise UnauthorizedException("User not found")

    return user


def require_permission(permission: str):
    """
    Dependency checking permission claim directly from Access Token payload without DB query.
    """
    def dependency(payload: dict = Depends(get_access_payload)):
        permissions = payload.get("permissions", [])
        if permission not in permissions:
            raise ForbiddenException("Permission denied")
        return payload

    return dependency


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.ADMIN.value:
        raise ForbiddenException("Access restricted to Admins only")
    return current_user


def require_investor(current_user: User = Depends(get_current_user)) -> User:
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.INVESTOR.value:
        raise ForbiddenException("Access restricted to Investors only")
    return current_user


def authorize_user_or_admin(
    user_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
) -> User:
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val == UserRole.ADMIN.value:
        return current_user

    if current_user.uuid != user_id:
        raise ForbiddenException("Access restricted to admins and same user")
    return current_user