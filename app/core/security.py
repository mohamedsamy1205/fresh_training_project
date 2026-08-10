from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings


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

