from app.platform.users.model.user import User
from fastapi import Request, HTTPException, APIRouter, Depends
from app.platform.auth.service.auth_service import AuthService
from app.core.dependency_chain import get_auth_service
from app.core.security import get_user_from_refrsh_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/refresh",
    summary="Refresh access token",
    description="""
    Public endpoint.

    Refreshes the JWT access token using the refresh_token cookie.
    """
)
def refresh(service: AuthService = Depends(get_auth_service), current_user: User = Depends(get_user_from_refrsh_token)):

    return service.refresh_token(current_user)