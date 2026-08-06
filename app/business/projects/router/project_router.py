from fastapi import APIRouter, Depends, status
from app.business.projects.model.project import Project
from datetime import datetime, timedelta
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.core.security import require_admin, require_investor
from app.platform.users.model.user import User
from app.business.projects.schema.project_schema import (
    ProjectCreate,
    ProjectResponse,
    ProjectCloseRequest,
    CreateInvestmentRequest,
    InvestmentRequestResponse,
    DistributeProfitsRequest,
    ProjectAnalyticsResponse
)
from app.business.projects.service.project_service import ProjectService

admin_router = APIRouter(
    prefix="/admin/projects",
    tags=["Admin Projects"]
)

investor_router = APIRouter(
    prefix="/investor/projects",
    tags=["Investor Projects"]
)

def get_project_service(db=Depends(get_db)) -> ProjectService:
    return ProjectService(db)

# ======================= ADMIN ENDPOINTS =======================

@admin_router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create investment project",
    description="""
    Admin only endpoint.

    Allows administrators to create a new investment project
    with start date and end date.
    """
)
def create_project(
    request: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(require_admin)
):
    return service.create_project(
        name=request.name,
        start_date=request.start_date,
        end_date=request.end_date
    )

@admin_router.get(
    "/{project_id}/analytics",
    response_model=ProjectAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project investment analytics",
    description="""
    Admin only endpoint.

    Retrieves aggregated investment analytics, total capital, and performance metrics for a specific project.
    """
)
def get_project_analytics(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(require_admin)
):
    return service.get_project_analytics(project_id=project_id)

@admin_router.post(
    "/requests/{request_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve investment request",
    description="""
    Admin only endpoint.

    Allows administrators to approve an investor's pending investment request using an idempotency key.
    """
)
def approve_investment_request(
    request_id: UUID,
    idempotency_key: str,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(require_admin)
):
    return service.approve_investment_request(
        request_id=request_id,
        idempotency_key=idempotency_key
    )

@admin_router.post(
    "/requests/{request_id}/reject",
    response_model=InvestmentRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject investment request",
    description="""
    Admin only endpoint.

    Allows administrators to reject an investor's pending investment request.
    """
)
def reject_investment_request(
    request_id: UUID,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(require_admin)
):
    return service.reject_investment_request(
        request_id=request_id
    )

@admin_router.post(
    "/{project_id}/close",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Close active project",
    description="""
    Admin only endpoint.

    Closes an active investment project and sets the final valuation amount.
    Requires a minimum of 2 active investors.
    """
)
def close_project(
    project_id: UUID,
    request: ProjectCloseRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(require_admin)
):
    return service.close_project(
        project_id=project_id,
        final_amount=request.final_amount
    )

@admin_router.post(
    "/{project_id}/distribute-profits",
    status_code=status.HTTP_200_OK,
    summary="Distribute project profits/losses",
    description="""
    Admin only endpoint.

    Distributes financial profits or losses to project investors proportionally using an idempotency key.
    """
)
def distribute_profits(
    project_id: UUID,
    request: DistributeProfitsRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(require_admin)
):
    return service.distribute_profits(
        project_id=project_id,
        idempotency_key=request.idempotency_key
    )

# ======================= INVESTOR ENDPOINTS =======================

@investor_router.post(
    "/{project_id}/investment-requests",
    response_model=InvestmentRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit investment request",
    description="""
    Investor endpoint.

    Allows registered investors to submit an investment request for a specific project.
    """
)
def create_investment_request(
    project_id: UUID,
    request: CreateInvestmentRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(require_investor)
):
    return service.create_investment_request(
        user_id=current_user.uuid,
        project_id=project_id,
        wallet_id=request.wallet_id,
        amount=request.amount
    )

router = APIRouter()
router.include_router(admin_router)
router.include_router(investor_router)



@router.get("/projects", response_model=List[ProjectResponse])
def list_all_projects(db=Depends(get_db)):
    return db.query(Project).all()

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project_generic(
    payload: dict,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(require_admin)
):
    name = payload.get("name")
    start_date = payload.get("start_date") or datetime.utcnow()
    end_date = payload.get("end_date") or (datetime.utcnow() + timedelta(days=365))
    return service.create_project(name=name, start_date=start_date, end_date=end_date)

