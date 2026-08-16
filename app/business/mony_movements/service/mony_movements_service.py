import uuid
from decimal import Decimal
from typing import Dict, Any, Tuple, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.business.wallet.model.wallet import Wallet
from app.business.transaction.model.transaction import Transaction
from app.business.transaction.model.ledger_entry import LedgerEntry
from app.common.enums import (
    TransactionType,
    TransactionStatus,
    LedgerEntryType
)
from app.core.config import settings
from app.core.exceptions import (
    ResourceNotFoundException,
    InsufficientBalanceException,
    InvalidOperationException,
    DuplicateOperationException
)


class MoneyMovementsService:
    """
    Handles all financial and money-related operations including:
    - User and treasury wallet balance mutations and deterministic locking
    - Double-entry ledger entries and transaction lifecycle tracking
    - Idempotent deposits and withdrawals
    - Project investment fund transfers
    - Project closure valuation deposits
    - Investor profit and loss distribution payouts with company fees
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # WALLET LOOKUPS & CONCURRENCY LOCKING
    # =========================================================================

    def get_treasury_wallet(self) -> Wallet:
        """Retrieves the main company treasury wallet."""
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

    def _get_treasury_wallet(self) -> Wallet:
        return self.get_treasury_wallet()

    def get_user_wallet(self, user_id: UUID) -> Wallet:
        """Retrieves a user's wallet by user ID."""
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

    def _get_user_wallet(self, user_id: UUID) -> Wallet:
        return self.get_user_wallet(user_id)

    def get_wallet_by_id(self, wallet_id: UUID, user_id: Optional[UUID] = None) -> Wallet:
        """Retrieves a wallet by UUID, optionally validating user ownership."""
        query = self.db.query(Wallet).filter(Wallet.uuid == wallet_id)
        if user_id:
            query = query.filter(Wallet.user_id == user_id)
        wallet = query.first()
        if wallet is None:
            if user_id:
                raise ResourceNotFoundException(f"Wallet '{wallet_id}' not found for user '{user_id}'.")
            raise ResourceNotFoundException(f"Wallet '{wallet_id}' not found.")
        return wallet

    def lock_wallets(self, *wallet_ids: UUID) -> Tuple[Wallet, ...]:
        """
        Locks multiple wallets deterministically by sorted UUID to prevent deadlocks.
        Returns the locked wallet instances in the exact order requested.
        """
        sorted_ids = sorted(list(wallet_ids), key=lambda x: str(x))
        wallets = (
            self.db.query(Wallet)
            .filter(Wallet.uuid.in_(sorted_ids))
            .order_by(Wallet.uuid.asc())
            .with_for_update()
            .all()
        )

        wallet_map = {wallet.uuid: wallet for wallet in wallets}

        try:
            return tuple(wallet_map[w_id] for w_id in wallet_ids)
        except KeyError as exc:
            raise ResourceNotFoundException(
                "One or more wallets were not found."
            ) from exc

    def _lock_wallets(self, first_wallet_id: UUID, second_wallet_id: UUID) -> Tuple[Wallet, Wallet]:
        res = self.lock_wallets(first_wallet_id, second_wallet_id)
        return res[0], res[1]

    def lock_single_wallet(self, wallet_id: UUID) -> Wallet:
        """Locks a single wallet with row-level lock (SELECT FOR UPDATE)."""
        wallet = (
            self.db.query(Wallet)
            .filter(Wallet.uuid == wallet_id)
            .with_for_update()
            .first()
        )
        if wallet is None:
            raise ResourceNotFoundException(f"Investor wallet '{wallet_id}' not found.")
        return wallet

    # =========================================================================
    # VALIDATION HELPERS
    # =========================================================================

    def validate_amount(self, amount: Decimal, allow_zero: bool = False) -> Decimal:
        """Validates that the amount is a valid Decimal and meets positivity constraints."""
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        if allow_zero:
            if amount < Decimal("0.00"):
                raise InvalidOperationException("Amount must be non-negative.")
        else:
            if amount <= Decimal("0.00"):
                raise InvalidOperationException(
                    f"Invalid transaction amount '{amount}'. "
                    "Amount must be strictly greater than 0."
                )

        return amount

    def _validate_amount(self, amount: Decimal) -> Decimal:
        return self.validate_amount(amount)

    def validate_sufficient_balance(
        self,
        wallet: Wallet,
        amount: Decimal,
        message: str = "Insufficient user balance"
    ) -> None:
        """Validates that a wallet has sufficient balance for a deduction."""
        if wallet.balance < amount:
            raise InsufficientBalanceException(message)

    def _validate_withdrawal(self, user_wallet: Wallet, amount: Decimal) -> None:
        self.validate_sufficient_balance(user_wallet, amount, "Insufficient user balance")

    def check_idempotency(self, idempotency_key: str) -> Optional[Transaction]:
        """Checks if a transaction with the given idempotency key already exists."""
        return (
            self.db.query(Transaction)
            .filter(Transaction.idempotency_key == idempotency_key)
            .first()
        )

    def _check_idempotency(self, idempotency_key: str) -> Optional[Transaction]:
        return self.check_idempotency(idempotency_key)

    # =========================================================================
    # TRANSACTION & LEDGER FACTORIES
    # =========================================================================

    def create_transaction(
        self,
        *,
        user_id: Optional[UUID],
        wallet_id: UUID,
        amount: Decimal,
        movement_type: TransactionType,
        idempotency_key: str,
        status: TransactionStatus = TransactionStatus.SUCCESS,
        currency: str = "USD",
        description: Optional[str] = None,
    ) -> Transaction:
        """Creates and flushes a Transaction record."""
        tx_type_val = movement_type.value if hasattr(movement_type, "value") else str(movement_type)
        tx_status_val = status.value if hasattr(status, "value") else str(status)

        tx = Transaction(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=amount,
            currency=currency,
            type=tx_type_val,
            status=tx_status_val,
            idempotency_key=idempotency_key,
            description=description,
        )
        self.db.add(tx)
        self.db.flush()
        return tx

    def _create_transaction(
        self,
        *,
        user_id: Optional[UUID],
        wallet_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        movement_type: TransactionType,
        description: Optional[str],
    ) -> Transaction:
        return self.create_transaction(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=amount,
            movement_type=movement_type,
            idempotency_key=idempotency_key,
            description=description,
        )

    def create_ledger_entry(
        self,
        *,
        transaction: Transaction,
        wallet: Wallet,
        entry_type: LedgerEntryType,
        amount: Decimal,
    ) -> LedgerEntry:
        """Creates and stages a double-entry LedgerEntry record."""
        entry_type_val = entry_type.value if hasattr(entry_type, "value") else str(entry_type)

        entry = LedgerEntry(
            transaction_id=transaction.uuid,
            wallet_id=wallet.uuid,
            entry_type=entry_type_val,
            amount=amount,
            balance_after=wallet.balance,
        )
        self.db.add(entry)
        return entry

    def _create_ledger_entry(
        self,
        *,
        transaction: Transaction,
        wallet: Wallet,
        entry_type: LedgerEntryType,
        amount: Decimal,
    ) -> LedgerEntry:
        return self.create_ledger_entry(
            transaction=transaction,
            wallet=wallet,
            entry_type=entry_type,
            amount=amount,
        )

    # =========================================================================
    # CORE FINANCIAL OPERATIONS
    # =========================================================================

    def deposit(
        self,
        user_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Admin deposit funds into a user wallet and treasury."""
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
        """Admin withdraw funds from a user wallet and treasury."""
        return self._execute(
            user_id=user_id,
            amount=amount,
            idempotency_key=idempotency_key,
            movement_type=TransactionType.WITHDRAW,
            description=description,
        )

    def _apply_balance_change(
        self,
        movement_type: TransactionType,
        user_wallet: Wallet,
        treasury_wallet: Wallet,
        amount: Decimal,
    ) -> None:
        if movement_type == TransactionType.DEPOSIT:
            user_wallet.balance += amount
            treasury_wallet.balance += amount
        elif movement_type == TransactionType.WITHDRAW:
            user_wallet.balance -= amount
            treasury_wallet.balance -= amount

    def _execute(
        self,
        *,
        user_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        movement_type: TransactionType,
        description: Optional[str],
    ) -> Dict[str, Any]:
        amount = self.validate_amount(amount)

        existing = self.check_idempotency(idempotency_key)
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

        user_wallet = self.get_user_wallet(user_id)
        treasury_wallet = self.get_treasury_wallet()

        try:
            with self.db.begin_nested():
                user_wallet, treasury_wallet = self.lock_wallets(
                    user_wallet.uuid,
                    treasury_wallet.uuid,
                )

                if movement_type == TransactionType.WITHDRAW:
                    self.validate_sufficient_balance(user_wallet, amount)

                self._apply_balance_change(
                    movement_type,
                    user_wallet,
                    treasury_wallet,
                    amount,
                )

                tx = self.create_transaction(
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

                user_entry = self.create_ledger_entry(
                    transaction=tx,
                    wallet=user_wallet,
                    entry_type=entry_type,
                    amount=amount,
                )

                treasury_entry = self.create_ledger_entry(
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

    # =========================================================================
    # PROJECT-RELATED FINANCIAL OPERATIONS
    # =========================================================================

    def process_investment(
        self,
        *,
        user_id: UUID,
        wallet_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        project_name: str,
    ) -> Transaction:
        """
        Executes financial transfer for an approved investment:
        - Locks investor and treasury wallets deterministically
        - Validates investor wallet balance
        - Debits investor wallet, credits treasury wallet
        - Records INVESTMENT transaction and double-entry ledger records
        """
        treasury_wallet = self.get_treasury_wallet()

        user_w_locked, treasury_w_locked = self.lock_wallets(
            wallet_id,
            treasury_wallet.uuid,
        )

        self.validate_sufficient_balance(
            user_w_locked,
            amount,
            message="Insufficient balance in investor wallet."
        )

        user_w_locked.balance -= amount
        treasury_w_locked.balance += amount

        tx = self.create_transaction(
            user_id=user_id,
            wallet_id=user_w_locked.uuid,
            amount=amount,
            currency=user_w_locked.currency or "USD",
            movement_type=TransactionType.INVESTMENT,
            status=TransactionStatus.SUCCESS,
            idempotency_key=idempotency_key,
            description=f"Approved investment in project {project_name}",
        )

        self.create_ledger_entry(
            transaction=tx,
            wallet=user_w_locked,
            entry_type=LedgerEntryType.DEBIT,
            amount=amount,
        )

        self.create_ledger_entry(
            transaction=tx,
            wallet=treasury_w_locked,
            entry_type=LedgerEntryType.CREDIT,
            amount=amount,
        )

        self.db.flush()
        return tx

    def record_project_closure(
        self,
        *,
        project_uuid: UUID,
        project_name: str,
        final_amount: Decimal,
    ) -> Tuple[Transaction, LedgerEntry]:
        """
        Records the financial deposit into treasury upon project closure.
        """
        treasury_wallet = self.get_treasury_wallet()
        treasury_wallet.balance += final_amount

        tx = self.create_transaction(
            user_id=None,
            wallet_id=treasury_wallet.uuid,
            amount=final_amount,
            currency=treasury_wallet.currency or "USD",
            movement_type=TransactionType.DEPOSIT,
            status=TransactionStatus.SUCCESS,
            idempotency_key=f"close_project_{project_uuid}_{uuid.uuid4()}",
            description=f"Project closure valuation deposit for project {project_name}",
        )

        ledger_entry = self.create_ledger_entry(
            transaction=tx,
            wallet=treasury_wallet,
            entry_type=LedgerEntryType.CREDIT,
            amount=final_amount,
        )

        self.db.flush()
        return tx, ledger_entry

    def process_profit_payout(
        self,
        *,
        user_id: UUID,
        wallet_id: UUID,
        payout_amount: Decimal,
        company_fee: Decimal,
        payout_idempotency_key: str,
        fee_idempotency_key: str,
        project_name: str,
        treasury_wallet: Optional[Wallet] = None,
    ) -> Transaction:
        """
        Transfers investor payout from treasury to user wallet, creates ledger entries,
        and optionally records the company fee transaction.
        """
        treasury = treasury_wallet or self.get_treasury_wallet()
        user_wallet = self.lock_single_wallet(wallet_id)

        treasury.balance -= payout_amount
        user_wallet.balance += payout_amount
        self.db.flush()

        payout_tx = self.create_transaction(
            user_id=user_id,
            wallet_id=user_wallet.uuid,
            amount=payout_amount,
            currency=user_wallet.currency or "USD",
            movement_type=TransactionType.PROFIT_PAYOUT,
            status=TransactionStatus.SUCCESS,
            idempotency_key=payout_idempotency_key,
            description=f"Profit payout for project {project_name}",
        )

        self.create_ledger_entry(
            transaction=payout_tx,
            wallet=treasury,
            entry_type=LedgerEntryType.DEBIT,
            amount=payout_amount,
        )

        self.create_ledger_entry(
            transaction=payout_tx,
            wallet=user_wallet,
            entry_type=LedgerEntryType.CREDIT,
            amount=payout_amount,
        )
        self.db.flush()

        if company_fee > Decimal("0.00"):
            self.create_transaction(
                user_id=user_id,
                wallet_id=treasury.uuid,
                amount=company_fee,
                currency=treasury.currency or "USD",
                movement_type=TransactionType.COMPANY_FEE,
                status=TransactionStatus.SUCCESS,
                idempotency_key=fee_idempotency_key,
                description=f"20% Company fee on profit for project {project_name}",
            )
            self.db.flush()

        return payout_tx

    # =========================================================================
    # SERIALIZATION HELPERS
    # =========================================================================

    def _build_response(
        self,
        transaction: Transaction,
        ledger_entries: List[LedgerEntry],
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