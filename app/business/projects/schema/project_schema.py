from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.common.enums import ProjectStatus, InvestmentRequestStatus

class ProjectCreate(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime

class ProjectCloseRequest(BaseModel):
    final_amount: Decimal = Field(..., gt=Decimal("0.00"), description="Final amount after project ends")

class CreateInvestmentRequest(BaseModel):
    wallet_id: UUID
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Requested investment amount")

class DistributeProfitsRequest(BaseModel):
    idempotency_key: str

class InvestmentRequestResponse(BaseModel):
    uuid: UUID
    user_id: UUID
    project_id: UUID
    wallet_id: UUID
    amount: Decimal
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
    amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    uuid: UUID
    name: str
    start_date: datetime
    end_date: datetime
    initial_amount: Decimal
    final_amount: Optional[Decimal] = None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectAnalyticsResponse(BaseModel):
    project_id: UUID
    project_name: str
    project_status: ProjectStatus
    initial_amount: Decimal
    total_invested_amount: Decimal
    number_of_investments: int
    number_of_unique_investors: int
    average_investment_amount: Decimal

    class Config:
        from_attributes = True
