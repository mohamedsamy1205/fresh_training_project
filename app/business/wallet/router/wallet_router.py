from fastapi import APIRouter, Depends
from app.core.dependency_chain import get_wallet_service
from app.core.store import require_investor, require_admin, authorize_user_or_admin
from app.business.wallet.schema.wallet_schema import WalletCreate, WalletUpdate, WalletResponse
from app.business.wallet.model.wallet import Wallet
from uuid import UUID
from typing import List
from app.business.wallet.service.wallet_service import WalletService
from app.platform.users.model.user import User

router = APIRouter(prefix="/wallet", tags=["Investor Wallet"])


@router.get(
    "/admin/{user_id}",
    response_model=List[WalletResponse],
    summary="Get wallet by user ID",
    description="""
    Investor endpoint.

    Retrieves wallet details and balances for a specified investor user ID.
    """
)
def get_by_user_id(
    user_id: UUID,
    current_user: User = Depends(authorize_user_or_admin),
    service: WalletService = Depends(get_wallet_service)
):
    return service.get_by_user_id(user_id)


@router.post(
    "/admin",
    response_model=WalletResponse,
    summary="Create investor wallet",
    description="""
    Investor endpoint.

    Creates a new wallet account for an investor.
    """
)
def create(
    data: WalletCreate,
    current_user: User = Depends(require_admin),
    service: WalletService = Depends(get_wallet_service)
):
    return service.create(data)



@router.get(
    "/wallets/me",
    response_model=List[WalletResponse],
    summary="Get current user wallet info"
)
def get_wallets_me(
    current_user: User = Depends(authorize_user_or_admin),
    service: WalletService = Depends(get_wallet_service)
):
    return service.get_by_user_id(current_user.uuid)

