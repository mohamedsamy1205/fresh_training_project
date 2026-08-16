from fastapi import Request, APIRouter, Depends, Response
from app.platform.auth.service.auth_service import AuthService
from app.core.dependency_chain import get_auth_service
from app.core.store import get_refresh_payload


def get_jwt_key_manager(request: Request):
    return request.app.state.jwt_key_manager


router = APIRouter(tags=["Auth"])


@router.post(
    "/refresh",
    summary="Refresh access token",
    description="""
    Public endpoint.

    Refreshes the JWT access token and refresh token using the refresh_token cookie and validates active session.
    """
)
def refresh(
    service: AuthService = Depends(get_auth_service),
    payload: dict = Depends(get_refresh_payload),
    key_manager=Depends(get_jwt_key_manager)
):
    response = Response(content="done")
    tokens = service.refresh_token(payload, key_manager)
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
def jwks(key_manager=Depends(get_jwt_key_manager)):
    return key_manager.get_jwks()