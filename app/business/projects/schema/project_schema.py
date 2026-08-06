from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.common.enums import ProjectStatus, InvestmentRequestStatus
from app.common.utils.money import MoneyAmount

class ProjectCreate(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime

class ProjectCloseRequest(BaseModel):
    final_amount: MoneyAmount = Field(..., gt=Decimal("0.00"), description="Final amount after project ends")

class CreateInvestmentRequest(BaseModel):
    wallet_id: UUID
    amount: MoneyAmount = Field(..., gt=Decimal("0.00"), description="Requested investment amount")

class DistributeProfitsRequest(BaseModel):
    idempotency_key: str

class InvestmentRequestResponse(BaseModel):
    uuid: UUID
    user_id: UUID
    project_id: UUID
    wallet_id: UUID
    amount: MoneyAmount
    status: InvestmentRequestStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InvestmentResponse(BaseModel):
    uuid: UUID
    user_id: UUID
    project_id: UUID
    wallet_id: UUID
    amount: MoneyAmount
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    uuid: UUID
    name: str
    start_date: datetime
    end_date: datetime
    initial_amount: MoneyAmount
    final_amount: Optional[MoneyAmount] = None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectAnalyticsResponse(BaseModel):
    project_id: UUID
    project_name: str
    project_status: ProjectStatus
    initial_amount: MoneyAmount
    total_invested_amount: MoneyAmount
    number_of_investments: int
    number_of_unique_investors: int
    average_investment_amount: MoneyAmount

    class Config:
        from_attributes = True
