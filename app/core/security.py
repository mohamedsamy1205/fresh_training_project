from fastapi import Request, Depends, HTTPException, status, Path
from fastapi.params import Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from app.core.database import get_db
from app.platform.users.model.user import User
from app.core.config import settings
from app.common.enums import UserRole
from uuid import UUID
from app.core.exceptions import UnauthorizedException, ForbiddenException, ResourceNotFoundException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_private_key():
    with open(settings.PRIVATE_KEY_PATH, "r") as f:
        PRIVATE_KEY = f.read()
    if isinstance(PRIVATE_KEY, str):
            PRIVATE_KEY = PRIVATE_KEY.encode()
    return PRIVATE_KEY

def get_public_key():
    with open(settings.PUBLIC_KEY_PATH, "r") as f:
        PUBLIC_KEY = f.read()
    if isinstance(PUBLIC_KEY, str):
        PUBLIC_KEY = PUBLIC_KEY.encode()
    return PUBLIC_KEY

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_private_key(), algorithm=settings.ALGORITHM, headers={"kid": "my-key-1"})

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_private_key(), algorithm=settings.ALGORITHM, headers={"kid": "my-key-1"})

def get_user_from_refrsh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("refresh_token")

    if not token:
        raise UnauthorizedException("Not authenticated")
    try:
        payload = jwt.decode(token, get_public_key(), algorithms=[settings.ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise UnauthorizedException("Invalid token payload")

        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise ResourceNotFoundException("User not found")

        return user

    except JWTError:
        raise UnauthorizedException("Invalid or expired token")

    
def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    token = request.cookies.get("access_token")

    if not token:
        raise UnauthorizedException("Not authenticated")

    try:
        payload = jwt.decode(token, get_public_key(), algorithms=[settings.ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise UnauthorizedException("Invalid token payload")

        user = db.query(User).filter(User.email == email).first()

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