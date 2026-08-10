from app.platform.users.model.user import User
from fastapi import Request, HTTPException, APIRouter, Depends
from app.platform.auth.service.auth_service import AuthService
from app.core.dependency_chain import get_auth_service
from app.core.store import get_user_from_refrsh_token
from fastapi import Response

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
    response = Response(content="done")
    tokens = service.refresh_token(current_user)
    access_value = tokens["access_token"]
    refresh_value = tokens["refresh_token"]
    response.set_cookie(
        key="access_token",
        value=access_value,
        httponly=True,
        secure=False,  
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_value,
        httponly=True,
        secure=False,  
        samesite="lax"
    )
    return response

@router.get("/.well-known/jwks.json")
def jwks(service: AuthService = Depends(get_auth_service)):
    return service.jwks()