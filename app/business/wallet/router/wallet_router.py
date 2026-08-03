from fastapi import APIRouter, Depends
from app.core.dependency_chain import get_wallet_service
from app.core.security import get_current_user
from app.business.wallet.schema.wallet_schema import WalletCreate, WalletUpdate, WalletResponse
from app.business.wallet.model.wallet import Wallet
from uuid import UUID
from typing import List
from app.business.wallet.service.wallet_service import WalletService
from app.platform.users.model.user import User

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/{user_id}", response_model=List[WalletResponse])
def get_by_user_id(user_id: UUID, current_user: User = Depends(get_current_user) , service: WalletService = Depends(get_wallet_service)):
    return service.get_by_user_id(user_id)

@router.post("/", response_model=WalletResponse)
def create(data: WalletCreate, current_user: User = Depends(get_current_user) , service: WalletService = Depends(get_wallet_service)):
    return service.create(data)

@router.post("/update_blance", response_model=WalletResponse)
def update_balance(data: WalletUpdate, current_user: User = Depends(get_current_user) , service: WalletService = Depends(get_wallet_service)):
    return service.update_balance(data)


