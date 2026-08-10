from app.core.exceptions import UnauthorizedException, ForbiddenException, ResourceNotFoundException
from jose import JWTError, jwt 
from app.platform.users.repository.user_repository import UserRepository
from fastapi import Request, Depends, Path
from app.core.redis import get_redis
from app.common.enums import UserRole
from uuid import UUID
from app.core.config import settings
from app.platform.users.model.user import User
from app.core.database import get_db

def get_user_repo(db=Depends(get_db), redis=Depends(get_redis)) -> UserRepository:
    return UserRepository(db,redis)

def get_public_key():
    with open(settings.PUBLIC_KEY_PATH, "r") as f:
        PUBLIC_KEY = f.read()
    if isinstance(PUBLIC_KEY, str):
        PUBLIC_KEY = PUBLIC_KEY.encode()
    return PUBLIC_KEY

def get_user_from_refrsh_token(
    request: Request,
    userRepository:UserRepository = Depends(get_user_repo)
):
    token = request.cookies.get("refresh_token")

    if not token:
        raise UnauthorizedException("Not authenticated")
    try:
        payload = jwt.decode(token, get_public_key(), algorithms=[settings.ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise UnauthorizedException("Invalid token payload")

        user = userRepository.get_by_email(email)

        if not user:
            raise ResourceNotFoundException("User not found")

        return user

    except JWTError:
        raise UnauthorizedException("Invalid or expired token")

    
def get_current_user(
    request: Request,
    userRepository:UserRepository = Depends(get_user_repo)
):
    token = request.cookies.get("access_token")

    if not token:
        raise UnauthorizedException("Not authenticated")

    try:
        payload = jwt.decode(token, get_public_key(), algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        
        if not email:
            raise UnauthorizedException("Invalid token payload")

        user = userRepository.get_by_email(email)

        if not user:
            raise ResourceNotFoundException("User not found")

        return user

    except JWTError:
        raise UnauthorizedException("Invalid or expired token")


def require_admin(current_user = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("Access restricted to Admins only")
    return current_user

def require_investor(current_user = Depends(get_current_user)):
    if current_user.role != UserRole.INVESTOR:
        raise ForbiddenException("Access restricted to Investors only")
    return current_user

def authorize_user_or_admin(
    user_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.ADMIN:
        return current_user
    
    if current_user.uuid != user_id:
        raise ForbiddenException("Access restricted to admins and same user")
    return current_user