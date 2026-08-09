from decimal import Decimal
from typing import Dict, Any, Tuple, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.core.exceptions import (
    ResourceNotFoundException,
    InsufficientBalanceException,
    InvalidOperationException,
    DuplicateOperationException
)

from app.business.wallet.model.wallet import Wallet
from app.business.transaction.model.transaction import Transaction
from app.business.transaction.model.ledger_entry import LedgerEntry
from app.common.enums import WalletType, TransactionType, TransactionStatus, LedgerEntryType
from app.core.config import settings
from uuid import UUID
from decimal import Decimal
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.business.transaction.model.transaction import Transaction
from app.business.transaction.model.ledger_entry import LedgerEntry
from app.business.transaction.schema.transaction_schema import TransactionType, TransactionStatus


class MoneyMovementsService:
    """
    Handles financial money movements between user and treasury wallets.

    The service uses the database session injected by FastAPI and keeps
    wallet mutations, transactions, and ledger entries within the same
    unit of work.
    """

    def __init__(self, db: Session):
        self.db = db

    def deposit(
        self,
        user_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._execute(
            user_id=user_id,
            amount=amount,
            idempotency_key=idempotency_key,
            movement_type=TransactionType.DEPOSIT,
            description=description,
        )

    def withdraw(
        self,
        user_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._execute(
            user_id=user_id,
            amount=amount,
            idempotency_key=idempotency_key,
            movement_type=TransactionType.WITHDRAW,
            description=description,
        )

    def _validate_amount(self, amount: Decimal) -> Decimal:
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        if amount <= Decimal("0"):
            raise InvalidOperationException(
                f"Invalid transaction amount '{amount}'. "
                "Amount must be strictly greater than 0."
            )

        return amount

    def _get_treasury_wallet(self) -> Wallet:
        wallet = (
            self.db.query(Wallet)
            .filter(Wallet.uuid == settings.MAIN_COMPANY_WALLET)
            .first()
        )

        if wallet is None:
            raise ResourceNotFoundException(
                "Company treasury wallet not found."
            )

        return wallet

    def _get_user_wallet(self, user_id: UUID) -> Wallet:
        wallet = (
            self.db.query(Wallet)
            .filter(Wallet.user_id == user_id)
            .first()
        )

        if wallet is None:
            raise ResourceNotFoundException(
                f"User wallet not found for user ID: {user_id}"
            )

        return wallet

    def _lock_wallets(
        self,
        first_wallet_id: UUID,
        second_wallet_id: UUID,
    ) -> tuple[Wallet, Wallet]:

        wallet_ids = sorted(
            [first_wallet_id, second_wallet_id],
            key=str,
        )

        wallets = (
            self.db.query(Wallet)
            .filter(Wallet.uuid.in_(wallet_ids))
            .order_by(Wallet.uuid.asc())
            .with_for_update()
            .all()
        )

        wallet_map = {
            wallet.uuid: wallet
            for wallet in wallets
        }

        try:
            return (
                wallet_map[first_wallet_id],
                wallet_map[second_wallet_id],
            )
        except KeyError as exc:
            raise ResourceNotFoundException(
                "One or more wallets were not found."
            ) from exc


    def _check_idempotency(
        self,
        idempotency_key: str,
    ) -> Optional[Transaction]:

        return (
            self.db.query(Transaction)
            .filter(
                Transaction.idempotency_key == idempotency_key
            )
            .first()
        )

    def _validate_withdrawal(
        self,
        user_wallet: Wallet,
        amount: Decimal,
    ):
        if user_wallet.balance < amount:
            raise InsufficientBalanceException(
                "Insufficient user balance"
            )

    def _apply_balance_change(
        self,
        movement_type: TransactionType,
        user_wallet: Wallet,
        treasury_wallet: Wallet,
        amount: Decimal,
    ):
        if movement_type == TransactionType.DEPOSIT:
            user_wallet.balance += amount
            treasury_wallet.balance += amount

        elif movement_type == TransactionType.WITHDRAW:
            user_wallet.balance -= amount
            treasury_wallet.balance -= amount

    def _create_transaction(
        self,
        *,
        user_id: UUID,
        wallet_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        movement_type: TransactionType,
        description: Optional[str],
    ) -> Transaction:

        tx = Transaction(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=amount,
            currency="USD",
            type=movement_type.value,
            status=TransactionStatus.SUCCESS.value,
            idempotency_key=idempotency_key,
            description=description,
        )

        self.db.add(tx)
        self.db.flush()

        return tx
    def _create_ledger_entry(
        self,
        *,
        transaction: Transaction,
        wallet: Wallet,
        entry_type: LedgerEntryType,
        amount: Decimal,
    ) -> LedgerEntry:

        entry = LedgerEntry(
            transaction_id=transaction.uuid,
            wallet_id=wallet.uuid,
            entry_type=entry_type.value,
            amount=amount,
            balance_after=wallet.balance,
        )

        self.db.add(entry)

        return entry

    def _build_response(
        self,
        transaction: Transaction,
        ledger_entries: list[LedgerEntry],
        duplicate: bool = False,
    ) -> Dict[str, Any]:

        return {
            "success": True,
            "duplicate": duplicate,
            "transaction": self._serialize_transaction(transaction),
            "ledger_entries": [
                self._serialize_ledger_entry(le)
                for le in ledger_entries
            ],
        }

    def _serialize_transaction(self, tx: Transaction) -> Dict[str, Any]:
        return {
            "uuid": str(tx.uuid),
            "idempotency_key": tx.idempotency_key, 
            "user_id": str(tx.user_id) if tx.user_id else None,
            "wallet_id": str(tx.wallet_id),
            "amount": tx.amount,
            "currency": tx.currency,
            "type": tx.type,
            "status": tx.status,
            "description": tx.description,
            "created_at": tx.created_at.isoformat()
            if tx.created_at else None,
        }


    def _serialize_ledger_entry(self, le: LedgerEntry) -> Dict[str, Any]:
        return {
            "uuid": str(le.uuid),
            "transaction_id": str(le.transaction_id),
            "wallet_id": str(le.wallet_id),
            "entry_type": le.entry_type,
            "amount": le.amount,
            "balance_after": le.balance_after,
            "created_at": le.created_at.isoformat()
            if le.created_at else None,
        }

    def _execute(
        self,
        *,
        user_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        movement_type: TransactionType,
        description: Optional[str],
    ) -> Dict[str, Any]:

        amount = self._validate_amount(amount)

        existing = self._check_idempotency(idempotency_key)
        if existing:
            ledger_entries = (
                self.db.query(LedgerEntry)
                .filter(LedgerEntry.transaction_id == existing.uuid)
                .all()
            )
            return self._build_response(
                existing,
                ledger_entries,
                duplicate=True,
            )

        user_wallet = self._get_user_wallet(user_id)
        treasury_wallet = self._get_treasury_wallet()

        try:
            with self.db.begin_nested():

                user_wallet, treasury_wallet = self._lock_wallets(
                    user_wallet.uuid,
                    treasury_wallet.uuid,
                )

                if movement_type == TransactionType.WITHDRAW:
                    self._validate_withdrawal(
                        user_wallet,
                        amount,
                    )

                self._apply_balance_change(
                    movement_type,
                    user_wallet,
                    treasury_wallet,
                    amount,
                )

                tx = self._create_transaction(
                    user_id=user_id,
                    wallet_id=user_wallet.uuid,
                    amount=amount,
                    idempotency_key=idempotency_key,
                    movement_type=movement_type,
                    description=description,
                )

                entry_type = (
                    LedgerEntryType.CREDIT
                    if movement_type == TransactionType.DEPOSIT
                    else LedgerEntryType.DEBIT
                )

                user_entry = self._create_ledger_entry(
                    transaction=tx,
                    wallet=user_wallet,
                    entry_type=entry_type,
                    amount=amount,
                )

                treasury_entry = self._create_ledger_entry(
                    transaction=tx,
                    wallet=treasury_wallet,
                    entry_type=entry_type,
                    amount=amount,
                )

                self.db.flush()

            self.db.commit()

            return self._build_response(
                tx,
                [user_entry, treasury_entry],
            )

        except Exception:
            self.db.rollback()
            raise