import uuid
from decimal import Decimal
from unittest.mock import MagicMock
import pytest

from app.business.mony_movements.service.mony_movements_service import MoneyMovementsService
from app.business.wallet.model.wallet import Wallet
from app.business.transaction.model.transaction import Transaction
from app.business.transaction.model.ledger_entry import LedgerEntry
from app.common.enums import TransactionType, TransactionStatus, LedgerEntryType
from app.core.exceptions import (
    ResourceNotFoundException,
    InsufficientBalanceException,
    InvalidOperationException
)
from app.core.config import settings


def test_validate_amount_valid():
    db = MagicMock()
    service = MoneyMovementsService(db)

    assert service.validate_amount(Decimal("100.50")) == Decimal("100.50")
    assert service.validate_amount("50.00") == Decimal("50.00")


def test_validate_amount_zero_and_negative_raises():
    db = MagicMock()
    service = MoneyMovementsService(db)

    with pytest.raises(InvalidOperationException):
        service.validate_amount(Decimal("0.00"), allow_zero=False)

    with pytest.raises(InvalidOperationException):
        service.validate_amount(Decimal("-10.00"), allow_zero=False)


def test_validate_amount_allow_zero():
    db = MagicMock()
    service = MoneyMovementsService(db)

    assert service.validate_amount(Decimal("0.00"), allow_zero=True) == Decimal("0.00")
    with pytest.raises(InvalidOperationException):
        service.validate_amount(Decimal("-1.00"), allow_zero=True)


def test_get_treasury_wallet_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    service = MoneyMovementsService(db)

    with pytest.raises(ResourceNotFoundException):
        service.get_treasury_wallet()


def test_get_user_wallet_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    service = MoneyMovementsService(db)

    with pytest.raises(ResourceNotFoundException):
        service.get_user_wallet(uuid.uuid4())


def test_validate_sufficient_balance_raises():
    db = MagicMock()
    service = MoneyMovementsService(db)

    wallet = Wallet(uuid=uuid.uuid4(), balance=Decimal("50.00"))
    with pytest.raises(InsufficientBalanceException):
        service.validate_sufficient_balance(wallet, Decimal("100.00"))


def test_process_investment_success():
    db = MagicMock()
    service = MoneyMovementsService(db)

    user_id = uuid.uuid4()
    wallet_id = uuid.uuid4()
    treasury_id = settings.MAIN_COMPANY_WALLET

    mock_investor_wallet = Wallet(uuid=wallet_id, user_id=user_id, balance=Decimal("500.00"), currency="USD")
    mock_treasury_wallet = Wallet(uuid=treasury_id, balance=Decimal("10000.00"), currency="USD")

    # 1. get_treasury_wallet query
    # 2. lock_wallets query
    db.query.return_value.filter.return_value.first.return_value = mock_treasury_wallet
    db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.all.return_value = [
        mock_investor_wallet,
        mock_treasury_wallet
    ]

    tx = service.process_investment(
        user_id=user_id,
        wallet_id=wallet_id,
        amount=Decimal("200.00"),
        idempotency_key=str(uuid.uuid4()),
        project_name="Solar Energy"
    )

    assert mock_investor_wallet.balance == Decimal("300.00")
    assert mock_treasury_wallet.balance == Decimal("10200.00")
    assert tx.amount == Decimal("200.00")
    assert tx.type == TransactionType.INVESTMENT.value
    assert db.add.called
    assert db.flush.called


def test_process_investment_insufficient_balance():
    db = MagicMock()
    service = MoneyMovementsService(db)

    user_id = uuid.uuid4()
    wallet_id = uuid.uuid4()
    treasury_id = settings.MAIN_COMPANY_WALLET

    mock_investor_wallet = Wallet(uuid=wallet_id, user_id=user_id, balance=Decimal("50.00"), currency="USD")
    mock_treasury_wallet = Wallet(uuid=treasury_id, balance=Decimal("10000.00"), currency="USD")

    db.query.return_value.filter.return_value.first.return_value = mock_treasury_wallet
    db.query.return_value.filter.return_value.order_by.return_value.with_for_update.return_value.all.return_value = [
        mock_investor_wallet,
        mock_treasury_wallet
    ]

    with pytest.raises(InsufficientBalanceException):
        service.process_investment(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=Decimal("200.00"),
            idempotency_key=str(uuid.uuid4()),
            project_name="Solar Energy"
        )


def test_record_project_closure():
    db = MagicMock()
    service = MoneyMovementsService(db)

    treasury_id = settings.MAIN_COMPANY_WALLET
    mock_treasury_wallet = Wallet(uuid=treasury_id, balance=Decimal("10000.00"), currency="USD")
    db.query.return_value.filter.return_value.first.return_value = mock_treasury_wallet

    project_id = uuid.uuid4()
    tx, ledger = service.record_project_closure(
        project_uuid=project_id,
        project_name="Solar Energy",
        final_amount=Decimal("5000.00")
    )

    assert mock_treasury_wallet.balance == Decimal("15000.00")
    assert tx.type == TransactionType.DEPOSIT.value
    assert tx.amount == Decimal("5000.00")
    assert ledger.entry_type == LedgerEntryType.CREDIT.value
    assert ledger.balance_after == Decimal("15000.00")


def test_process_profit_payout_with_fee():
    db = MagicMock()
    service = MoneyMovementsService(db)

    treasury_id = settings.MAIN_COMPANY_WALLET
    user_id = uuid.uuid4()
    wallet_id = uuid.uuid4()

    mock_treasury_wallet = Wallet(uuid=treasury_id, balance=Decimal("20000.00"), currency="USD")
    mock_user_wallet = Wallet(uuid=wallet_id, user_id=user_id, balance=Decimal("100.00"), currency="USD")

    db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_user_wallet

    payout_tx = service.process_profit_payout(
        user_id=user_id,
        wallet_id=wallet_id,
        payout_amount=Decimal("1200.00"),
        company_fee=Decimal("40.00"),
        payout_idempotency_key="payout_key_1",
        fee_idempotency_key="fee_key_1",
        project_name="Solar Energy",
        treasury_wallet=mock_treasury_wallet
    )

    assert mock_treasury_wallet.balance == Decimal("18800.00")
    assert mock_user_wallet.balance == Decimal("1300.00")
    assert payout_tx.amount == Decimal("1200.00")
    assert payout_tx.type == TransactionType.PROFIT_PAYOUT.value
    assert db.add.called
    assert db.flush.called
