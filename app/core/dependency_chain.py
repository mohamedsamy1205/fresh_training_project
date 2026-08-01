from fastapi import Depends
from app.core.database import get_db
from app.platform.users.repository.user_repository import UserRepository
from app.platform.users.service.user_service import UserService
from app.platform.auth.service.auth_service import AuthService

# ====================== USER SERVICE ======================

def get_user_repo(db=Depends(get_db)):
    return UserRepository(db)

def get_user_service(repo=Depends(get_user_repo)):
    return UserService(repo)

# ====================== AUTH SERVICE ======================

def get_auth_service(user_service: UserService = Depends(get_user_service)):
    return AuthService(user_service)