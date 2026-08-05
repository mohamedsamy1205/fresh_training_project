from fastapi import Request, HTTPException, APIRouter, Depends
from app.platform.auth.service.auth_service import AuthService
from app.core.dependency_chain import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/refresh",
    summary="Refresh access token",
    description="""
    Public endpoint.

    Refreshes the JWT access token using the refresh_token cookie.
    """
)
def refresh(request: Request, service: AuthService = Depends(get_auth_service)):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    return service.refresh_token(refresh_token)