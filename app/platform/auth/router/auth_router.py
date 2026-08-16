from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Request, Depends, Response, Path
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

from app.core.config import settings
from app.core.store import get_current_user, get_access_payload, decode_token
from app.core.dependency_chain import get_auth_service
from app.platform.auth.service.auth_service import AuthService
from app.platform.auth.router import local_auth_router
from app.platform.auth.schemas.schemas import SessionResponse, MessageResponse
from app.platform.users.model.user import User


def get_jwt_key_manager(request: Request):
    return request.app.state.jwt_key_manager


def extract_client_info(request: Request) -> dict:
    user_agent = request.headers.get("user-agent", "")
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    elif request.client:
        ip_address = request.client.host
    else:
        ip_address = None

    device_name = None
    if user_agent:
        ua_lower = user_agent.lower()
        if "iphone" in ua_lower:
            device_name = "iPhone"
        elif "ipad" in ua_lower:
            device_name = "iPad"
        elif "android" in ua_lower:
            device_name = "Android Device"
        elif "macintosh" in ua_lower or "mac os" in ua_lower:
            device_name = "Mac"
        elif "windows" in ua_lower:
            device_name = "Windows PC"
        elif "linux" in ua_lower:
            device_name = "Linux PC"
        else:
            device_name = "Desktop / Browser"

    return {
        "user_agent": user_agent or None,
        "ip_address": ip_address,
        "device_name": device_name,
    }


router = APIRouter(prefix="/auth", tags=["Auth"])
router.include_router(local_auth_router.router)

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url=settings.SERVER_METADATA_URL,
    client_kwargs={
        "scope": "openid email profile"
    },
)


@router.get(
    "/google/login",
    summary="Initiate Google OAuth2 login",
    description="""
    Public endpoint.

    Redirects the user to the Google OAuth2 authentication page for login.
    """
)
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get(
    "/google/callback",
    summary="Google OAuth2 authentication callback",
    description="""
    Public endpoint.

    Handles the OAuth2 callback from Google, authenticates the user,
    creates a session, and sets access and refresh tokens in HTTP-only cookies.
    """
)
async def google_callback(
    request: Request,
    service: AuthService = Depends(get_auth_service),
    key_manager=Depends(get_jwt_key_manager)
):
    token = await oauth.google.authorize_access_token(request)
    response = RedirectResponse(url="/")

    user_info = token.get("userinfo")
    client_info = extract_client_info(request)

    tokens = service.login_with_google(user_info, key_manager, client_info=client_info)
    access_value = tokens["access_token"]
    refresh_value = tokens["refresh_token"]

    response.set_cookie(
        key="access_token",
        value=access_value,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_value,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response


@router.get(
    "/me",
    summary="Get current logged in user details",
    description="Returns user profile and role for auto-auth check."
)
def get_me(current_user: User = Depends(get_current_user)):
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    return {
        "uuid": str(current_user.uuid),
        "name": current_user.name,
        "email": current_user.email,
        "role": role_str,
    }


@router.get(
    "/sessions",
    response_model=List[SessionResponse],
    summary="List active user sessions",
    description="Lists all active authentication sessions for the currently authenticated user."
)
def list_sessions(
    payload: dict = Depends(get_access_payload),
    service: AuthService = Depends(get_auth_service),
):
    user_id = payload.get("user_id")
    current_sid = payload.get("sid")
    return service.get_user_sessions(user_id=user_id, current_sid=current_sid)


@router.delete(
    "/sessions/{session_id}",
    response_model=MessageResponse,
    summary="Revoke a specific session",
    description="Revokes a single session by session UUID. Users can only revoke their own sessions."
)
def revoke_session(
    response: Response,
    session_id: UUID = Path(..., description="UUID of the session to revoke"),
    payload: dict = Depends(get_access_payload),
    service: AuthService = Depends(get_auth_service),
):
    user_id = payload.get("user_id")
    current_sid = payload.get("sid")

    res = service.revoke_session(user_id=user_id, session_id=session_id)

    if current_sid and str(session_id) == str(current_sid):
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

    return res


@router.delete(
    "/sessions",
    response_model=MessageResponse,
    summary="Revoke all user sessions",
    description="Revokes all active sessions for the currently authenticated user and clears auth cookies."
)
def revoke_all_sessions(
    response: Response,
    payload: dict = Depends(get_access_payload),
    service: AuthService = Depends(get_auth_service),
):
    user_id = payload.get("user_id")
    res = service.revoke_all_sessions(user_id=user_id)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return res


@router.post(
    "/logout",
    summary="Logout user",
    description="Revokes current session and clears access and refresh token HttpOnly cookies."
)
def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    key_manager=Depends(get_jwt_key_manager),
):
    # Attempt to revoke session if token is valid
    token = request.cookies.get("access_token") or request.cookies.get("refresh_token")
    if token:
        try:
            payload = decode_token(token, key_manager)
            user_id = payload.get("user_id")
            sid = payload.get("sid")
            if user_id and sid:
                service.revoke_session(user_id=user_id, session_id=sid)
        except Exception:
            pass

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}