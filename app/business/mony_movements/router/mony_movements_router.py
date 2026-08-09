from fastapi import APIRouter, Depends, status
from app.core.database import get_db
from app.core.security import require_admin
from app.platform.users.model.user import User
from app.business.mony_movements.schema.money_movement_schema import (
    DepositRequest,
    WithdrawRequest,
    MoneyMovementResponse
)
from app.business.mony_movements.service.mony_movements_service import MoneyMovementsService

router = APIRouter(
    prefix="/admin/money-movements",
    tags=["Admin Money Movements"]
)

def get_money_movement_service(db = Depends(get_db)) -> MoneyMovementsService:
    return MoneyMovementsService(db)


@router.post(
    "/deposit",
    response_model=MoneyMovementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deposit funds into user wallet",
    description="""
    Admin only endpoint.

    Allows administrators to deposit funds directly into a user's wallet using an idempotency key.
    """
)
def deposit(
    request: DepositRequest,
    service: MoneyMovementsService = Depends(get_money_movement_service),
    current_user: User = Depends(require_admin)
):
    return service.deposit(
        user_id=request.user_id,
        amount=request.amount,
        idempotency_key=request.idempotency_key,
        description=request.description
    )


@router.post(
    "/withdraw",
    response_model=MoneyMovementResponse,
    status_code=status.HTTP_200_OK,
    summary="Withdraw funds from user wallet",
    description="""
    Admin only endpoint.

    Allows administrators to withdraw funds from a user's wallet using an idempotency key.
    """
)
def withdraw(
    request: WithdrawRequest,
    service: MoneyMovementsService = Depends(get_money_movement_service),
    current_user: User = Depends(require_admin)
):
    return service.withdraw(
        user_id=request.user_id,
        amount=request.amount,
        idempotency_key=request.idempotency_key,
        description=request.description
    )
