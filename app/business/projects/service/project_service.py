import json
from decimal import Decimal
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.business.projects.model.project import Project
from app.business.projects.model.investment import Investment
from app.business.projects.model.investment_request import InvestmentRequest
from app.business.projects.schema.project_schema import ProjectResponse
from app.business.mony_movements.service.mony_movements_service import MoneyMovementsService
from app.common.enums import (
    UserRole,
    ProjectStatus,
    InvestmentRequestStatus,
)
from app.core.exceptions import (
    ResourceNotFoundException,
    InvalidOperationException,
    AppException
)


class ProjectService:
    """
    Service handling Projects, Investment Requests, Approvals, Closures, Analytics, and Profit Distribution.

    Financial and monetary operations (wallet lookups, balance mutations, locking,
    transactions, and ledger entries) are delegated to MoneyMovementsService.
    """

    def __init__(
        self,
        db: Session,
        redis: Optional[Any] = None,
        money_movement_service: Optional[MoneyMovementsService] = None
    ):
        self.db = db
        self.redis = redis
        self.money_movement_service = money_movement_service or MoneyMovementsService(db)

    # =========================================================================
    # PROJECT LIFECYCLE & DISCOVERY
    # =========================================================================

    async def list_all_projects(self, current_user: Optional[Any] = None) -> List[Dict[str, Any]]:
        """Lists all projects with Redis caching and investor-specific status enrichment."""
        cache_key = "projects"
        cached = None
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
            except Exception:
                cached = None

        if cached:
            data = json.loads(cached)
        else:
            query = self.db.query(Project).all()
            data = [
                ProjectResponse.model_validate(project).model_dump(mode="json")
                for project in query
            ]
            if self.redis:
                try:
                    await self.redis.setex(cache_key, 300, json.dumps(data))
                except Exception:
                    pass

        if current_user and getattr(current_user, "uuid", None):
            user_role = getattr(current_user, "role", None)
            role_str = user_role.value if hasattr(user_role, "value") else str(user_role or "")
            if role_str.lower() == UserRole.INVESTOR.value:
                user_requests = (
                    self.db.query(InvestmentRequest)
                    .filter(InvestmentRequest.user_id == current_user.uuid)
                    .order_by(InvestmentRequest.created_at.desc())
                    .all()
                )
                req_map = {}
                for req in user_requests:
                    p_id = str(req.project_id)
                    if p_id not in req_map:
                        status_val = req.status.value if hasattr(req.status, "value") else str(req.status)
                        req_map[p_id] = status_val

                updated_data = []
                for p in data:
                    p_copy = dict(p)
                    p_copy["user_request_status"] = req_map.get(str(p_copy.get("uuid")))
                    updated_data.append(p_copy)
                return updated_data

        return data

    async def create_project(self, name: str, start_date: datetime, end_date: datetime) -> Project:
        """Creates a new investment project."""
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

        if self.redis:
            try:
                await self.redis.delete("projects")
            except Exception:
                pass

        self.db.refresh(project)
        return project

    async def delete_project(self, project_id: UUID) -> Dict[str, Any]:
        """Transactionally deletes a project and its associated investment requests and investments."""
        project = (
            self.db.query(Project)
            .filter(Project.uuid == project_id)
            .first()
        )
        if not project:
            raise ResourceNotFoundException(f"Project '{project_id}' not found.")

        try:
            with self.db.begin_nested():
                self.db.query(InvestmentRequest).filter(
                    InvestmentRequest.project_id == project_id
                ).delete(synchronize_session=False)

                self.db.query(Investment).filter(
                    Investment.project_id == project_id
                ).delete(synchronize_session=False)

                self.db.delete(project)
                self.db.flush()

            self.db.commit()

            if self.redis:
                try:
                    await self.redis.delete("projects")
                except Exception:
                    pass

            return {
                "success": True,
                "message": f"Project '{project_id}' and all associated relations deleted successfully."
            }

        except AppException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise InvalidOperationException(f"Failed to delete project: {str(e)}")

    # =========================================================================
    # INVESTMENT REQUESTS
    # =========================================================================

    def create_investment_request(
        self,
        user_id: UUID,
        project_id: UUID,
        wallet_id: UUID,
        amount: Decimal
    ) -> InvestmentRequest:
        """Allows an investor to submit an investment request for an active project."""
        valid_amount = self.money_movement_service.validate_amount(amount)

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

        # Validate wallet exists and belongs to the user
        self.money_movement_service.get_wallet_by_id(wallet_id, user_id=user_id)

        existing_request = (
            self.db.query(InvestmentRequest)
            .filter(
                InvestmentRequest.user_id == user_id,
                InvestmentRequest.project_id == project.uuid
            )
            .first()
        )
        if existing_request:
            req_status = (
                existing_request.status.value
                if hasattr(existing_request.status, "value")
                else str(existing_request.status)
            )
            raise InvalidOperationException(
                f"You have already submitted an investment request for this project (Status: {req_status.upper()})."
            )

        investment_request = InvestmentRequest(
            user_id=user_id,
            project_id=project.uuid,
            wallet_id=wallet_id,
            amount=valid_amount,
            status=InvestmentRequestStatus.PENDING.value
        )
        self.db.add(investment_request)
        self.db.commit()
        self.db.refresh(investment_request)
        return investment_request

    def list_investment_requests(self, project_id: UUID) -> List[InvestmentRequest]:
        """Lists all investment requests for a specific project."""
        project = (
            self.db.query(Project)
            .filter(Project.uuid == project_id)
            .first()
        )
        if not project:
            raise ResourceNotFoundException(f"Project '{project_id}' not found.")

        return (
            self.db.query(InvestmentRequest)
            .filter(InvestmentRequest.project_id == project_id)
            .all()
        )

    async def approve_investment_request(
        self,
        request_id: UUID,
        idempotency_key: str
    ) -> Dict[str, Any]:
        """
        Approves an investor's pending investment request:
        - Validates project and request status
        - Delegates financial movement to MoneyMovementsService
        - Creates Investment record
        - Updates project initial_amount and request status
        """
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

        valid_amount = inv_request.amount

        try:
            with self.db.begin_nested():
                # Delegate wallet debit/credit, locking, transaction & ledger creation to Money Movements
                tx = self.money_movement_service.process_investment(
                    user_id=inv_request.user_id,
                    wallet_id=inv_request.wallet_id,
                    amount=valid_amount,
                    idempotency_key=idempotency_key,
                    project_name=project.name,
                )

                project.initial_amount += valid_amount

                investment = Investment(
                    user_id=inv_request.user_id,
                    project_id=project.uuid,
                    wallet_id=inv_request.wallet_id,
                    amount=valid_amount
                )
                self.db.add(investment)
                self.db.flush()

                inv_request.status = InvestmentRequestStatus.APPROVED.value
                self.db.flush()

            self.db.commit()

            if self.redis:
                try:
                    await self.redis.delete("projects")
                except Exception:
                    pass

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
        """Rejects an investor's pending investment request."""
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

    # =========================================================================
    # PROJECT CLOSURE & VALUATION
    # =========================================================================

    async def close_project(self, project_id: UUID, final_amount: Decimal) -> Project:
        """
        Closes an active investment project:
        - Validates final valuation amount and investor participation (>= 2 investors)
        - Delegates treasury deposit to MoneyMovementsService
        - Updates project status to CLOSED and sets final_amount
        """
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

        try:
            with self.db.begin_nested():
                # Delegate financial deposit and transaction/ledger creation to Money Movements
                self.money_movement_service.record_project_closure(
                    project_uuid=project.uuid,
                    project_name=project.name,
                    final_amount=final_amount,
                )

                project.final_amount = final_amount
                project.status = ProjectStatus.CLOSED.value
                self.db.flush()

            self.db.commit()

            if self.redis:
                try:
                    await self.redis.delete("projects")
                except Exception:
                    pass

            self.db.refresh(project)
            return project

        except AppException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise InvalidOperationException(f"Failed to close project: {str(e)}")

    # =========================================================================
    # ANALYTICS & PROFIT DISTRIBUTION
    # =========================================================================

    def get_project_analytics(self, project_id: UUID) -> Dict[str, Any]:
        """Calculates real-time project investment metrics and performance analytics."""
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

    async def distribute_profits(
        self,
        project_id: UUID,
        idempotency_key: str
    ) -> Dict[str, Any]:
        """
        Distributes profits/losses proportionally to all project investors:
        - Calculates pro-rata shares, net profits, and 20% company cut on positive profits
        - Delegates individual financial payouts to MoneyMovementsService
        - Updates project status to DISTRIBUTED
        """
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

        treasury_wallet = self.money_movement_service.get_treasury_wallet()

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
                    investor_gross_profit = total_profit * share_ratio

                    if is_profitable:
                        company_fee = investor_gross_profit * company_cut_rate
                        investor_net_profit = investor_gross_profit - company_fee
                    else:
                        company_fee = Decimal("0.00")
                        investor_net_profit = investor_gross_profit

                    investor_total_payout = Decimal(str(inv.amount)) + investor_net_profit

                    total_company_fee_collected += company_fee
                    total_returned_to_investors += investor_total_payout

                    # Delegate financial movement to Money Movements Service
                    self.money_movement_service.process_profit_payout(
                        user_id=inv.user_id,
                        wallet_id=inv.wallet_id,
                        payout_amount=investor_total_payout,
                        company_fee=company_fee,
                        payout_idempotency_key=f"{idempotency_key}_payout_{inv.uuid}",
                        fee_idempotency_key=f"{idempotency_key}_fee_{inv.uuid}",
                        project_name=project.name,
                        treasury_wallet=treasury_wallet,
                    )

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

            if self.redis:
                try:
                    await self.redis.delete("projects")
                except Exception:
                    pass

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
