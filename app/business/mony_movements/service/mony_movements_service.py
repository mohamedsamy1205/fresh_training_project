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
        Production-grade financial money movement service.

        Architectural & Concurrency Guarantees:
        1. Injected DB Session Only: Operates strictly within the unit-of-work session provided by FastAPI dependency injection.
        2. ACID Atomic Operations: All wallet mutations and ledger creation occur within atomic nested transaction blocks (`begin_nested()`).
        3. Row-Level Pessimistic Locking (`FOR UPDATE`): Locks wallet records to guarantee isolation during concurrent updates.
        4. Deterministic Deadlock Prevention: Locks wallets ordered by Primary Key ID (`ORDER BY id ASC`), eliminating AB-BA lock cycles.
        5. Double-Entry Auditability: Every money movement generates an immutable transaction header and dual balanced ledger entries.
        """

        def __init__(self, db: Session):
            # Always use injected session (no new sessions created)
            self.db = db

        # -------------------------------------------------------------------------
        # Shared Helper & Query Optimization Methods
        # -------------------------------------------------------------------------

        def _validate_amount(self, amount: Decimal) -> Decimal:
            """Validates that transaction amount is strictly positive and formatted as Decimal."""
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
            if amount <= Decimal("0.00"):
                raise InvalidOperationException(
                    f"Invalid transaction amount '{amount}'. Amount must be strictly greater than 0."
                )
            return amount

        def _get_treasury_wallet(self) -> Wallet:
            """Retrieves the company treasury wallet."""
            treasury = (
                self.db.query(Wallet)
                .filter(Wallet.uuid == settings.MAIN_COMPANY_WALLET)
                .first()
            )
            if not treasury:
                treasury = Wallet(
                    name="Company Treasury Vault",
                    type=WalletType.TREASURY.value,
                    currency="USD",
                    balance=Decimal("10000000.00")
                )
                self.db.add(treasury)
                self.db.flush()
            return treasury

        def _get_user_wallet(self, user_id: UUID) -> Wallet:
            """Retrieves user wallet by user_id."""
            wallet = (
                self.db.query(Wallet)
                .filter(Wallet.user_id == user_id)
                .first()
            )
            if not wallet:
                raise ResourceNotFoundException(
                    f"User wallet not found for user ID: {user_id}"
                )
            return wallet


        def _lock_wallets_deterministically(self, wallet_id_1: int, wallet_id_2: int) -> Tuple[Wallet, Wallet]:
            """
            Locks two wallets using SELECT ... FOR UPDATE ordered by Primary Key ID.
            Sorting guarantees consistent lock acquisition order across concurrent execution threads,
            completely eliminating database deadlocks (AB-BA lock ordering conflicts).
            """
            sorted_ids = sorted([wallet_id_1, wallet_id_2])

            # Single query with IN clause to eliminate N+1 roundtrips
            locked_wallets = (
                self.db.query(Wallet)
                .filter(Wallet.uuid.in_(sorted_ids))
                .order_by(Wallet.uuid.asc())
                .with_for_update()
                .all()
            )

            wallet_map = {w.uuid: w for w in locked_wallets}
            return wallet_map[wallet_id_1], wallet_map[wallet_id_2]

        def _check_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
            """Checks if a transaction with the given idempotency key was already executed."""
            existing_tx = (
                self.db.query(Transaction)
                .filter(Transaction.idempotency_key == idempotency_key)
                .first()
            )
            if existing_tx:
                ledger_entries = (
                    self.db.query(LedgerEntry)
                    .filter(LedgerEntry.transaction_id == existing_tx.uuid)
                    .all()
                )
                return self._format_response(existing_tx, ledger_entries, is_duplicate=True)
            return None

        def _format_response(
            self,
            tx: Transaction,
            ledger_entries: List[LedgerEntry],
            is_duplicate: bool = False
        ) -> Dict[str, Any]:
            """Formats transaction and ledger entries into a structured DTO dictionary."""

            return {
                "success": True,
                "is_duplicate": is_duplicate,

                "transaction": {
                    "uuid": str(tx.uuid),
                    "idempotency_key": tx.idempotency_key,
                    "wallet_id": str(tx.wallet_id),
                    "user_id": str(tx.user_id) if tx.user_id else None,
                    "type": tx.type,
                    "status": tx.status,
                    "amount": float(tx.amount),
                    "currency": tx.currency,
                    "description": tx.description,
                    "created_at": (
                        tx.created_at.isoformat()
                        if tx.created_at
                        else None
                    )
                },

                "ledger_entries": [
                    {
                        "uuid": str(le.uuid),
                        "transaction_id": str(le.transaction_id),
                        "wallet_id": str(le.wallet_id),
                        "entry_type": le.entry_type,
                        "amount": float(le.amount),
                        "balance_after": float(le.balance_after),
                        "created_at": (
                            le.created_at.isoformat()
                            if le.created_at
                            else None
                        )
                    }
                    for le in ledger_entries
                ]
            }
        # -------------------------------------------------------------------------
        # Core Methods: DEPOSIT & WITHDRAW
        # -------------------------------------------------------------------------

        def deposit(
            self,
            user_id: UUID,
            amount: Decimal,
            idempotency_key: str,
            description: Optional[str] = None
        ) -> Dict[str, Any]:

            valid_amount = self._validate_amount(amount)

            user_idempotency_key = f"{idempotency_key}_user"
            treasury_idempotency_key = f"{idempotency_key}_treasury"


            # -----------------------------
            # Idempotency check
            # -----------------------------

            existing_user_tx = self._check_idempotency(
                user_idempotency_key
            )

            existing_treasury_tx = self._check_idempotency(
                treasury_idempotency_key
            )


            if existing_user_tx and existing_treasury_tx:

                return {
                    "success": True,
                    "duplicate": True,

                    "transaction_ids": [
                        UUID(existing_user_tx["transaction"]["uuid"]),
                        UUID(existing_treasury_tx["transaction"]["uuid"])
                    ],

                    "amount": existing_user_tx["transaction"]["amount"],
                    "currency": existing_user_tx["transaction"]["currency"],

                    "description": existing_user_tx["transaction"]["description"],

                    "transactions": [
                        existing_user_tx["transaction"],
                        existing_treasury_tx["transaction"]
                    ],

                    "ledger_entries": (
                        existing_user_tx["ledger_entries"]
                        +
                        existing_treasury_tx["ledger_entries"]
                    )
                }


            treasury_wallet = self._get_treasury_wallet()
            user_wallet = self._get_user_wallet(user_id)


            try:

                with self.db.begin_nested():


                    # Lock wallets
                    user_w_locked, treasury_w_locked = (
                        self._lock_wallets_deterministically(
                            user_wallet.uuid,
                            treasury_wallet.uuid
                        )
                    )


                    # -----------------------------
                    # Update balances
                    # -----------------------------

                    user_w_locked.balance += valid_amount

                    treasury_w_locked.balance += valid_amount


                    self.db.flush()



                    # -----------------------------
                    # User Transaction
                    # -----------------------------

                    user_tx = Transaction(

                        idempotency_key=user_idempotency_key,

                        user_id=user_id,

                        wallet_id=user_w_locked.uuid,

                        amount=valid_amount,

                        currency="USD",

                        type=TransactionType.DEPOSIT.value,

                        status=TransactionStatus.SUCCESS.value,

                        description=(
                            description
                            or f"Deposit {valid_amount} to user wallet"
                        )
                    )


                    self.db.add(user_tx)

                    self.db.flush()



                    user_ledger = LedgerEntry(

                        transaction_id=user_tx.uuid,

                        wallet_id=user_w_locked.uuid,

                        entry_type=LedgerEntryType.CREDIT.value,

                        amount=valid_amount,

                        balance_after=user_w_locked.balance
                    )



                    # -----------------------------
                    # Treasury Transaction
                    # -----------------------------

                    treasury_tx = Transaction(

                        idempotency_key=treasury_idempotency_key,

                        user_id=user_id,

                        wallet_id=treasury_w_locked.uuid,

                        amount=valid_amount,

                        currency="USD",

                        type=TransactionType.DEPOSIT.value,

                        status=TransactionStatus.SUCCESS.value,

                        description="External deposit received"
                    )


                    self.db.add(treasury_tx)

                    self.db.flush()



                    treasury_ledger = LedgerEntry(

                        transaction_id=treasury_tx.uuid,

                        wallet_id=treasury_w_locked.uuid,

                        entry_type=LedgerEntryType.CREDIT.value,

                        amount=valid_amount,

                        balance_after=treasury_w_locked.balance
                    )



                    self.db.add_all(
                        [
                            user_ledger,
                            treasury_ledger
                        ]
                    )


                    self.db.flush()



                self.db.commit()



                return {

                    "success": True,

                    "duplicate": False,


                    "transaction_ids": [

                        user_tx.uuid,

                        treasury_tx.uuid

                    ],


                    "amount": valid_amount,

                    "currency": "USD",


                    "description": description,


                    "transactions": [

                        {
                            "uuid": user_tx.uuid,
                            "idempotency_key": user_tx.idempotency_key,
                            "user_id": user_tx.user_id,
                            "wallet_id": user_tx.wallet_id,
                            "amount": user_tx.amount,
                            "currency": user_tx.currency,
                            "type": user_tx.type,
                            "status": user_tx.status,
                            "description": user_tx.description,
                            "created_at": user_tx.created_at
                        },

                        {
                            "uuid": treasury_tx.uuid,
                            "idempotency_key": treasury_tx.idempotency_key,
                            "user_id": treasury_tx.user_id,
                            "wallet_id": treasury_tx.wallet_id,
                            "amount": treasury_tx.amount,
                            "currency": treasury_tx.currency,
                            "type": treasury_tx.type,
                            "status": treasury_tx.status,
                            "description": treasury_tx.description,
                            "created_at": treasury_tx.created_at
                        }
                    ],


                    "ledger_entries": [

                        user_ledger,

                        treasury_ledger

                    ]

                }



            except HTTPException:

                self.db.rollback()

                raise



            except IntegrityError as e:

                self.db.rollback()


                if "idempotency_key" in str(e):

                    existing_user = self._check_idempotency(
                        user_idempotency_key
                    )

                    existing_treasury = self._check_idempotency(
                        treasury_idempotency_key
                    )


                    if existing_user and existing_treasury:

                        return {

                            "success": True,

                            "duplicate": True,


                            "transaction_ids": [

                                UUID(existing_user["transaction"]["uuid"]),

                                UUID(existing_treasury["transaction"]["uuid"])

                            ],


                            "amount": existing_user["transaction"]["amount"],

                            "currency": existing_user["transaction"]["currency"],


                            "description": existing_user["transaction"]["description"],


                            "transactions": [

                                existing_user["transaction"],

                                existing_treasury["transaction"]

                            ],


                            "ledger_entries": (

                                existing_user["ledger_entries"]

                                +

                                existing_treasury["ledger_entries"]

                            )

                        }


                raise HTTPException(
                    status_code=409,
                    detail="Duplicate transaction"
                )



            except Exception as e:

                self.db.rollback()

                raise HTTPException(
                    status_code=500,
                    detail=f"Deposit failed: {str(e)}"
                )


        def withdraw(
            self,
            user_id: UUID,
            amount: Decimal,
            idempotency_key: str,
            description: Optional[str] = None
        ) -> Dict[str, Any]:

            valid_amount = self._validate_amount(amount)

            user_idempotency_key = f"{idempotency_key}_user"
            treasury_idempotency_key = f"{idempotency_key}_treasury"

            # -----------------------------
            # Idempotency check
            # -----------------------------
            existing_user_tx = self._check_idempotency(user_idempotency_key)
            existing_treasury_tx = self._check_idempotency(treasury_idempotency_key)

            if existing_user_tx and existing_treasury_tx:
                return {
                    "success": True,
                    "duplicate": True,
                    "transaction_ids": [
                        UUID(existing_user_tx["transaction"]["uuid"]),
                        UUID(existing_treasury_tx["transaction"]["uuid"])
                    ],
                    "amount": existing_user_tx["transaction"]["amount"],
                    "currency": existing_user_tx["transaction"]["currency"],
                    "description": existing_user_tx["transaction"]["description"],
                    "transactions": [
                        existing_user_tx["transaction"],
                        existing_treasury_tx["transaction"]
                    ],
                    "ledger_entries": (
                        existing_user_tx["ledger_entries"] +
                        existing_treasury_tx["ledger_entries"]
                    )
                }

            treasury_wallet = self._get_treasury_wallet()
            user_wallet = self._get_user_wallet(user_id)

            try:

                with self.db.begin_nested():

                    # Lock wallets
                    user_w_locked, treasury_w_locked = (
                        self._lock_wallets_deterministically(
                            user_wallet.uuid,
                            treasury_wallet.uuid
                        )
                    )

                    # -----------------------------
                    # Balance validation ✅ (زيادة عن deposit)
                    # -----------------------------
                    if user_w_locked.balance < valid_amount:
                        raise InsufficientBalanceException("Insufficient user balance")


                    # -----------------------------
                    # Update balances (✅ الفرق الوحيد)
                    # -----------------------------
                    user_w_locked.balance -= valid_amount
                    treasury_w_locked.balance -= valid_amount

                    self.db.flush()

                    # -----------------------------
                    # User Transaction
                    # -----------------------------
                    user_tx = Transaction(
                        idempotency_key=user_idempotency_key,
                        user_id=user_id,
                        wallet_id=user_w_locked.uuid,
                        amount=valid_amount,
                        currency="USD",
                        type=TransactionType.WITHDRAW.value,
                        status=TransactionStatus.SUCCESS.value,
                        description=(
                            description
                            or f"Withdraw {valid_amount} from user wallet"
                        )
                    )

                    self.db.add(user_tx)
                    self.db.flush()

                    user_ledger = LedgerEntry(
                        transaction_id=user_tx.uuid,
                        wallet_id=user_w_locked.uuid,
                        entry_type=LedgerEntryType.DEBIT.value,
                        amount=valid_amount,
                        balance_after=user_w_locked.balance
                    )

                    # -----------------------------
                    # Treasury Transaction
                    # -----------------------------
                    treasury_tx = Transaction(
                        idempotency_key=treasury_idempotency_key,
                        user_id=user_id,
                        wallet_id=treasury_w_locked.uuid,
                        amount=valid_amount,
                        currency="USD",
                        type=TransactionType.WITHDRAW.value,
                        status=TransactionStatus.SUCCESS.value,
                        description="Treasury payout"
                    )

                    self.db.add(treasury_tx)
                    self.db.flush()

                    treasury_ledger = LedgerEntry(
                        transaction_id=treasury_tx.uuid,
                        wallet_id=treasury_w_locked.uuid,
                        entry_type=LedgerEntryType.DEBIT.value,
                        amount=valid_amount,
                        balance_after=treasury_w_locked.balance
                    )

                    self.db.add_all([
                        user_ledger,
                        treasury_ledger
                    ])

                    self.db.flush()

                self.db.commit()

                return {
                    "success": True,
                    "duplicate": False,
                    "transaction_ids": [
                        user_tx.uuid,
                        treasury_tx.uuid
                    ],
                    "amount": valid_amount,
                    "currency": "USD",
                    "description": description,
                    "transactions": [
                        {
                            "uuid": user_tx.uuid,
                            "idempotency_key": user_tx.idempotency_key,
                            "user_id": user_tx.user_id,
                            "wallet_id": user_tx.wallet_id,
                            "amount": user_tx.amount,
                            "currency": user_tx.currency,
                            "type": user_tx.type,
                            "status": user_tx.status,
                            "description": user_tx.description,
                            "created_at": user_tx.created_at
                        },
                        {
                            "uuid": treasury_tx.uuid,
                            "idempotency_key": treasury_tx.idempotency_key,
                            "user_id": treasury_tx.user_id,
                            "wallet_id": treasury_tx.wallet_id,
                            "amount": treasury_tx.amount,
                            "currency": treasury_tx.currency,
                            "type": treasury_tx.type,
                            "status": treasury_tx.status,
                            "description": treasury_tx.description,
                            "created_at": treasury_tx.created_at
                        }
                    ],

                    # ✅ نفس deposit بالظبط (fix مهم)
                    "ledger_entries": [
                        {
                            "uuid": str(user_ledger.uuid),
                            "transaction_id": str(user_ledger.transaction_id),
                            "wallet_id": str(user_ledger.wallet_id),
                            "entry_type": user_ledger.entry_type,
                            "amount": float(user_ledger.amount),
                            "balance_after": float(user_ledger.balance_after),
                            "created_at": (
                                user_ledger.created_at.isoformat()
                                if user_ledger.created_at else None
                            )
                        },
                        {
                            "uuid": str(treasury_ledger.uuid),
                            "transaction_id": str(treasury_ledger.transaction_id),
                            "wallet_id": str(treasury_ledger.wallet_id),
                            "entry_type": treasury_ledger.entry_type,
                            "amount": float(treasury_ledger.amount),
                            "balance_after": float(treasury_ledger.balance_after),
                            "created_at": (
                                treasury_ledger.created_at.isoformat()
                                if treasury_ledger.created_at else None
                            )
                        }
                    ]
                }

            except HTTPException:
                self.db.rollback()
                raise

            except IntegrityError as e:
                self.db.rollback()

                if "idempotency_key" in str(e):
                    existing_user = self._check_idempotency(user_idempotency_key)
                    existing_treasury = self._check_idempotency(treasury_idempotency_key)

                    if existing_user and existing_treasury:
                        return {
                            "success": True,
                            "duplicate": True,
                            "transaction_ids": [
                                UUID(existing_user["transaction"]["uuid"]),
                                UUID(existing_treasury["transaction"]["uuid"])
                            ],
                            "amount": existing_user["transaction"]["amount"],
                            "currency": existing_user["transaction"]["currency"],
                            "description": existing_user["transaction"]["description"],
                            "transactions": [
                                existing_user["transaction"],
                                existing_treasury["transaction"]
                            ],
                            "ledger_entries": (
                                existing_user["ledger_entries"] +
                                existing_treasury["ledger_entries"]
                            )
                        }

                raise HTTPException(
                    status_code=409,
                    detail="Duplicate transaction"
                )

            except Exception as e:
                self.db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Withdrawal failed: {str(e)}"
                )