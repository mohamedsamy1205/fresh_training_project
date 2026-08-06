from decimal import Decimal
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.business.projects.model.project import Project
from app.business.projects.model.investment import Investment
from app.business.projects.model.investment_request import InvestmentRequest
from app.business.wallet.model.wallet import Wallet
from app.business.transaction.model.transaction import Transaction
from app.business.transaction.model.ledger_entry import LedgerEntry
from app.common.enums import (
    ProjectStatus,
    InvestmentRequestStatus,
    TransactionType,
    TransactionStatus,
    LedgerEntryType,
    WalletType
)
from app.core.config import settings
from app.core.exceptions import (
    ResourceNotFoundException,
    InsufficientBalanceException,
    InvalidOperationException,
    DuplicateOperationException,
    AppException
)

class ProjectService:
    """
    Production-grade service handling Projects, Investment Requests, Approvals, Closures, Analytics, and Profit Distribution.

    Guarantees:
    - Safe transactional execution (ACID) with nested atomic blocks.
    - Custom domain exceptions returning uniform JSON payloads.
    - Decimal precision for all financial operations.
    - DB-level aggregation for real-time analytics without memory overhead.
    """

    def __init__(self, db: Session):
        self.db = db

    def _validate_amount(self, amount: Decimal) -> Decimal:
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        if amount <= Decimal("0.00"):
            raise InvalidOperationException(
                f"Invalid amount '{amount}'. Must be strictly greater than 0."
            )
        return amount

    def _get_treasury_wallet(self) -> Wallet:
        treasury = (
            self.db.query(Wallet)
            .filter(Wallet.uuid == settings.MAIN_COMPANY_WALLET)
            .first()
        )
        if not treasury:
            treasury = Wallet(
                uuid=settings.MAIN_COMPANY_WALLET,
                name="Company Treasury Vault",
                type=WalletType.TREASURY.value,
                currency="USD",
                balance=Decimal("10000000.00")
            )
            self.db.add(treasury)
            self.db.flush()
        return treasury

    def _lock_wallets_deterministically(self, wallet_id_1: UUID, wallet_id_2: UUID):
        sorted_ids = sorted([wallet_id_1, wallet_id_2])
        locked_wallets = (
            self.db.query(Wallet)
            .filter(Wallet.uuid.in_(sorted_ids))
            .order_by(Wallet.uuid.asc())
            .with_for_update()
            .all()
        )
        wallet_map = {w.uuid: w for w in locked_wallets}
        return wallet_map[wallet_id_1], wallet_map[wallet_id_2]

    def create_project(self, name: str, start_date: datetime, end_date: datetime) -> Project:
        if end_date <= start_date:
            raise InvalidOperationException("end_date must be strictly after start_date.")
        project = Project(
            name=name,
            start_date=start_date,
            end_date=end_date,
            initial_amount=Decimal("0.00"),
            status=ProjectStatus.ACTIVE.value
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def create_investment_request(
        self,
        user_id: UUID,
        project_id: UUID,
        wallet_id: UUID,
        amount: Decimal
    ) -> InvestmentRequest:
        valid_amount = self._validate_amount(amount)

        project = (
            self.db.query(Project)
            .filter(Project.uuid == project_id)
            .first()
        )
        if not project:
            raise ResourceNotFoundException(f"Project '{project_id}' not found.")

        if project.status != ProjectStatus.ACTIVE.value:
            raise InvalidOperationException(
                f"Cannot submit investment request for project with status '{project.status}'."
            )

        now = datetime.utcnow()
        if now > project.end_date:
            raise InvalidOperationException("Investment window for this project has closed.")

        user_wallet = (
            self.db.query(Wallet)
            .filter(Wallet.uuid == wallet_id, Wallet.user_id == user_id)
            .first()
        )
        if not user_wallet:
            raise ResourceNotFoundException(f"Wallet '{wallet_id}' not found for user '{user_id}'.")

        investment_request = InvestmentRequest(
            user_id=user_id,
            project_id=project.uuid,
            wallet_id=user_wallet.uuid,
            amount=valid_amount,
            status=InvestmentRequestStatus.PENDING.value
        )
        self.db.add(investment_request)
        self.db.commit()
        self.db.refresh(investment_request)
        return investment_request

    def approve_investment_request(
        self,
        request_id: UUID,
        idempotency_key: str
    ) -> Dict[str, Any]:
        inv_request = (
            self.db.query(InvestmentRequest)
            .filter(InvestmentRequest.uuid == request_id)
            .first()
        )
        if not inv_request:
            raise ResourceNotFoundException(f"Investment request '{request_id}' not found.")

        if inv_request.status != InvestmentRequestStatus.PENDING.value:
            return {
                "success": True,
                "is_duplicate": True,
                "status": inv_request.status,
                "message": f"Investment request is already processed with status '{inv_request.status}'."
            }

        project = (
            self.db.query(Project)
            .filter(Project.uuid == inv_request.project_id)
            .first()
        )
        if not project or project.status != ProjectStatus.ACTIVE.value:
            raise InvalidOperationException("Project is no longer active for approval.")

        user_wallet = (
            self.db.query(Wallet)
            .filter(Wallet.uuid == inv_request.wallet_id)
            .first()
        )
        if not user_wallet:
            raise ResourceNotFoundException("Investor wallet not found.")

        treasury_wallet = self._get_treasury_wallet()
        valid_amount = inv_request.amount

        try:
            with self.db.begin_nested():
                user_w_locked, treasury_w_locked = self._lock_wallets_deterministically(
                    user_wallet.uuid, treasury_wallet.uuid
                )

                if user_w_locked.balance < valid_amount:
                    raise InsufficientBalanceException("Insufficient balance in investor wallet.")

                user_w_locked.balance -= valid_amount
                treasury_w_locked.balance += valid_amount
                project.initial_amount += valid_amount

                investment = Investment(
                    user_id=inv_request.user_id,
                    project_id=project.uuid,
                    wallet_id=user_w_locked.uuid,
                    amount=valid_amount
                )
                self.db.add(investment)
                self.db.flush()

                tx = Transaction(
                    idempotency_key=idempotency_key,
                    user_id=inv_request.user_id,
                    wallet_id=user_w_locked.uuid,
                    amount=valid_amount,
                    currency=user_w_locked.currency or "USD",
                    type=TransactionType.INVESTMENT.value,
                    status=TransactionStatus.SUCCESS.value,
                    description=f"Approved investment in project {project.name}"
                )
                self.db.add(tx)
                self.db.flush()

                user_ledger = LedgerEntry(
                    transaction_id=tx.uuid,
                    wallet_id=user_w_locked.uuid,
                    entry_type=LedgerEntryType.DEBIT.value,
                    amount=valid_amount,
                    balance_after=user_w_locked.balance
                )
                treasury_ledger = LedgerEntry(
                    transaction_id=tx.uuid,
                    wallet_id=treasury_w_locked.uuid,
                    entry_type=LedgerEntryType.CREDIT.value,
                    amount=valid_amount,
                    balance_after=treasury_w_locked.balance
                )
                self.db.add_all([user_ledger, treasury_ledger])

                inv_request.status = InvestmentRequestStatus.APPROVED.value
                self.db.flush()

            self.db.commit()

            return {
                "success": True,
                "is_duplicate": False,
                "request_id": str(inv_request.uuid),
                "status": inv_request.status,
                "investment_id": str(investment.uuid),
                "transaction_id": str(tx.uuid),
                "amount": valid_amount,
                "project_initial_amount": project.initial_amount
            }

        except AppException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise InvalidOperationException(f"Approval failed: {str(e)}")

    def reject_investment_request(self, request_id: UUID) -> InvestmentRequest:
        inv_request = (
            self.db.query(InvestmentRequest)
            .filter(InvestmentRequest.uuid == request_id)
            .first()
        )
        if not inv_request:
            raise ResourceNotFoundException(f"Investment request '{request_id}' not found.")

        if inv_request.status != InvestmentRequestStatus.PENDING.value:
            raise InvalidOperationException(f"Request is already in status '{inv_request.status}'.")

        inv_request.status = InvestmentRequestStatus.REJECTED.value
        self.db.commit()
        self.db.refresh(inv_request)
        return inv_request

    def close_project(self, project_id: UUID, final_amount: Decimal) -> Project:
        if not isinstance(final_amount, Decimal):
            final_amount = Decimal(str(final_amount))

        if final_amount < Decimal("0.00"):
            raise InvalidOperationException("final_amount must be non-negative.")

        project = (
            self.db.query(Project)
            .filter(Project.uuid == project_id)
            .first()
        )
        if not project:
            raise ResourceNotFoundException(f"Project '{project_id}' not found.")

        if project.status != ProjectStatus.ACTIVE.value:
            raise InvalidOperationException(
                f"Project status is '{project.status}', expected '{ProjectStatus.ACTIVE.value}' to close."
            )

        distinct_investors_count = (
            self.db.query(func.count(func.distinct(Investment.user_id)))
            .filter(Investment.project_id == project.uuid)
            .scalar()
        ) or 0

        if distinct_investors_count < 2:
            raise InvalidOperationException(
                f"Project cannot be closed: requires at least 2 distinct investors, but currently has {distinct_investors_count}."
            )

        project.final_amount = final_amount
        project.status = ProjectStatus.CLOSED.value
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project_analytics(self, project_id: UUID) -> Dict[str, Any]:
        project = (
            self.db.query(Project)
            .filter(Project.uuid == project_id)
            .first()
        )
        if not project:
            raise ResourceNotFoundException(f"Project '{project_id}' not found.")

        stats = (
            self.db.query(
                func.coalesce(func.sum(Investment.amount), Decimal("0.00")).label("total_invested"),
                func.count(Investment.id).label("num_investments"),
                func.count(func.distinct(Investment.user_id)).label("num_unique_investors")
            )
            .filter(Investment.project_id == project.uuid)
            .one()
        )

        total_invested = Decimal(str(stats.total_invested or "0.00"))
        num_investments = int(stats.num_investments or 0)
        num_unique_investors = int(stats.num_unique_investors or 0)

        if num_investments > 0:
            avg_investment = total_invested / Decimal(str(num_investments))
        else:
            avg_investment = Decimal("0.00")

        return {
            "project_id": project.uuid,
            "project_name": project.name,
            "project_status": project.status,
            "initial_amount": Decimal(str(project.initial_amount or "0.00")),
            "total_invested_amount": total_invested,
            "number_of_investments": num_investments,
            "number_of_unique_investors": num_unique_investors,
            "average_investment_amount": avg_investment
        }

    def distribute_profits(
        self,
        project_id: UUID,
        idempotency_key: str
    ) -> Dict[str, Any]:
        project = (
            self.db.query(Project)
            .filter(Project.uuid == project_id)
            .first()
        )
        if not project:
            raise ResourceNotFoundException(f"Project '{project_id}' not found.")

        if project.status == ProjectStatus.DISTRIBUTED.value:
            return {
                "success": True,
                "is_duplicate": True,
                "message": f"Profits for project '{project_id}' have already been distributed.",
                "project_status": project.status
            }

        if project.status != ProjectStatus.CLOSED.value:
            raise InvalidOperationException(
                f"Project must be in '{ProjectStatus.CLOSED.value}' status to distribute profits. Current status: '{project.status}'."
            )

        if project.initial_amount is None or project.initial_amount <= Decimal("0.00"):
            raise InvalidOperationException("Project has no investments (initial_amount is 0).")

        if project.final_amount is None:
            raise InvalidOperationException("Project final_amount is not set.")

        investments: List[Investment] = (
            self.db.query(Investment)
            .filter(Investment.project_id == project.uuid)
            .all()
        )

        if not investments:
            raise InvalidOperationException("No investment records found for this project.")

        treasury_wallet = self._get_treasury_wallet()

        total_initial = Decimal(str(project.initial_amount))
        total_final = Decimal(str(project.final_amount))
        total_profit = total_final - total_initial

        is_profitable = total_profit > Decimal("0.00")
        company_cut_rate = Decimal("0.20") if is_profitable else Decimal("0.00")

        distributions = []

        try:
            with self.db.begin_nested():
                total_company_fee_collected = Decimal("0.00")
                total_returned_to_investors = Decimal("0.00")

                for inv in investments:
                    share_ratio = Decimal(str(inv.amount)) / total_initial

                    if is_profitable:
                        investor_gross_profit = total_profit * share_ratio
                        company_fee = investor_gross_profit * company_cut_rate
                        investor_net_profit = investor_gross_profit - company_fee
                        investor_total_payout = Decimal(str(inv.amount)) + investor_net_profit
                    else:
                        investor_gross_profit = total_profit * share_ratio
                        company_fee = Decimal("0.00")
                        investor_net_profit = investor_gross_profit
                        investor_total_payout = Decimal(str(inv.amount)) + investor_net_profit

                    total_company_fee_collected += company_fee
                    total_returned_to_investors += investor_total_payout

                    user_wallet = (
                        self.db.query(Wallet)
                        .filter(Wallet.uuid == inv.wallet_id)
                        .with_for_update()
                        .first()
                    )

                    if not user_wallet:
                        raise ResourceNotFoundException(f"Investor wallet '{inv.wallet_id}' not found.")

                    treasury_wallet.balance -= investor_total_payout
                    user_wallet.balance += investor_total_payout
                    self.db.flush()

                    payout_tx_key = f"{idempotency_key}_payout_{inv.uuid}"
                    payout_tx = Transaction(
                        idempotency_key=payout_tx_key,
                        user_id=inv.user_id,
                        wallet_id=user_wallet.uuid,
                        amount=investor_total_payout,
                        currency=user_wallet.currency or "USD",
                        type=TransactionType.PROFIT_PAYOUT.value,
                        status=TransactionStatus.SUCCESS.value,
                        description=f"Profit payout for project {project.name}"
                    )
                    self.db.add(payout_tx)
                    self.db.flush()

                    treasury_ledger = LedgerEntry(
                        transaction_id=payout_tx.uuid,
                        wallet_id=treasury_wallet.uuid,
                        entry_type=LedgerEntryType.DEBIT.value,
                        amount=investor_total_payout,
                        balance_after=treasury_wallet.balance
                    )
                    user_ledger = LedgerEntry(
                        transaction_id=payout_tx.uuid,
                        wallet_id=user_wallet.uuid,
                        entry_type=LedgerEntryType.CREDIT.value,
                        amount=investor_total_payout,
                        balance_after=user_wallet.balance
                    )
                    self.db.add_all([treasury_ledger, user_ledger])
                    self.db.flush()

                    if company_fee > Decimal("0.00"):
                        fee_tx_key = f"{idempotency_key}_fee_{inv.uuid}"
                        fee_tx = Transaction(
                            idempotency_key=fee_tx_key,
                            user_id=inv.user_id,
                            wallet_id=treasury_wallet.uuid,
                            amount=company_fee,
                            currency=treasury_wallet.currency or "USD",
                            type=TransactionType.COMPANY_FEE.value,
                            status=TransactionStatus.SUCCESS.value,
                            description=f"20% Company fee on profit for project {project.name}"
                        )
                        self.db.add(fee_tx)
                        self.db.flush()

                    distributions.append({
                        "investment_id": str(inv.uuid),
                        "user_id": str(inv.user_id),
                        "wallet_id": str(inv.wallet_id),
                        "investment_amount": inv.amount,
                        "gross_profit": investor_gross_profit,
                        "company_fee": company_fee,
                        "net_profit": investor_net_profit,
                        "total_payout": investor_total_payout
                    })

                project.status = ProjectStatus.DISTRIBUTED.value
                self.db.flush()

            self.db.commit()

            return {
                "success": True,
                "is_duplicate": False,
                "project_id": str(project.uuid),
                "total_initial_amount": total_initial,
                "total_final_amount": total_final,
                "total_profit": total_profit,
                "total_company_fee_collected": total_company_fee_collected,
                "total_returned_to_investors": total_returned_to_investors,
                "distributions": distributions
            }

        except AppException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise InvalidOperationException(f"Profit distribution failed: {str(e)}")
