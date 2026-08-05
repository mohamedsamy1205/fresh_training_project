from fastapi import APIRouter, Depends
from app.core.dependency_chain import get_wallet_service
from app.core.security import require_investor
from app.business.wallet.schema.wallet_schema import WalletCreate, WalletUpdate, WalletResponse
from app.business.wallet.model.wallet import Wallet
from uuid import UUID
from typing import List
from app.business.wallet.service.wallet_service import WalletService
from app.platform.users.model.user import User

router = APIRouter(prefix="/investor/wallet", tags=["Investor Wallet"])


@router.get(
    "/{user_id}",
    response_model=List[WalletResponse],
    summary="Get wallet by user ID",
    description="""
    Investor endpoint.

    Retrieves wallet details and balances for a specified investor user ID.
    """
)
def get_by_user_id(
    user_id: UUID,
    current_user: User = Depends(require_investor),
    service: WalletService = Depends(get_wallet_service)
):
    return service.get_by_user_id(user_id)


@router.post(
    "",
    response_model=WalletResponse,
    summary="Create investor wallet",
    description="""
    Investor endpoint.

    Creates a new wallet account for an investor.
    """
)
def create(
    data: WalletCreate,
    current_user: User = Depends(require_investor),
    service: WalletService = Depends(get_wallet_service)
):
    return service.create(data)


@router.post(
    "/update_blance",
    response_model=WalletResponse,
    summary="Update wallet balance",
    description="""
    Investor endpoint.

    Updates the financial balance of an investor's wallet.
    """
)
def update_balance(
    data: WalletUpdate,
    current_user: User = Depends(require_investor),
    service: WalletService = Depends(get_wallet_service)
):
    return service.update_balance(data)
