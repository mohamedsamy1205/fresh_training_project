from fastapi import Depends
from app.core.redis import redis_client
from app.core.database import get_db
from app.platform.users.repository.user_repository import UserRepository
from app.platform.users.service.user_service import UserService
from app.platform.auth.service.auth_service import AuthService
from app.business.wallet.service.wallet_service import WalletService
from app.business.wallet.repository.wallet_repository import WalletRepository
from app.business.transaction.service.transaction_service import TransactionService
from app.business.transaction.repository.transaction_repository import TransactionRepository
from app.core.redis import get_redis


# ====================== USER SERVICE ======================

def get_user_repo(db = Depends(get_db), redis=Depends(get_redis)):
    return UserRepository(db,redis)

def get_user_service(repo: UserRepository =Depends(get_user_repo)):
    return UserService(repo)

# ====================== AUTH SERVICE ======================

def get_auth_service(user_service: UserService = Depends(get_user_service)):
    return AuthService(user_service)

# ====================== WALLET SERVICE ======================
def get_wallet_repo(db=Depends(get_db)):
    return WalletRepository(db)

def get_wallet_service(repo=Depends(get_wallet_repo)):
    return WalletService(repo)


# ====================== TRANSACTION SERVICE ======================
from app.business.transaction.controller.transaction_controller import TransactionController

def get_transaction_repo(db = Depends(get_db),redis=Depends(get_redis)) -> TransactionRepository:
    return TransactionRepository(db,redis)

def get_transaction_service(repo = Depends(get_transaction_repo)) -> TransactionService:
    return TransactionService(repo)

def get_transaction_controller(service = Depends(get_transaction_service)) -> TransactionController:
    return TransactionController(service)


# ====================== PROJECT SERVICE ======================
from app.business.projects.service.project_service import ProjectService

def get_project_service(db = Depends(get_db)) -> ProjectService:
    return ProjectService(db)

