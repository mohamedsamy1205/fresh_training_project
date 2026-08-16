from fastapi import Depends
from app.core.redis import redis_client
from app.core.database import get_db
from app.platform.users.repository.user_repository import UserRepository
from app.platform.users.service.user_service import UserService
from app.platform.auth.repository.session_repository import SessionRepository
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

# ====================== AUTH & SESSION SERVICE ======================

def get_session_repo(db = Depends(get_db), redis=Depends(get_redis)) -> SessionRepository:
    return SessionRepository(db, redis)

def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    session_repo: SessionRepository = Depends(get_session_repo),
) -> AuthService:
    return AuthService(user_service, session_repo)

# ====================== WALLET SERVICE ======================
def get_wallet_repo(db=Depends(get_db)):
    return WalletRepository(db)

def get_wallet_service(repo=Depends(get_wallet_repo)):
    return WalletService(repo)


# ====================== TRANSACTION SERVICE ======================

def get_transaction_repo(db = Depends(get_db),redis=Depends(get_redis)) -> TransactionRepository:
    return TransactionRepository(db,redis)

def get_transaction_service(repo = Depends(get_transaction_repo)) -> TransactionService:
    return TransactionService(repo)

# ====================== MONEY MOVEMENTS SERVICE ======================
from app.business.mony_movements.service.mony_movements_service import MoneyMovementsService

def get_money_movement_service(db = Depends(get_db)) -> MoneyMovementsService:
    return MoneyMovementsService(db)

# ====================== PROJECT SERVICE ======================
from app.business.projects.service.project_service import ProjectService

def get_project_service(
    db = Depends(get_db),
    redis = Depends(get_redis),
    money_movement_service: MoneyMovementsService = Depends(get_money_movement_service)
) -> ProjectService:
    return ProjectService(db, redis, money_movement_service)

