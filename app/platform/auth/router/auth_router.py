from fastapi import APIRouter, Request, Depends, Response
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from app.platform.auth.service.auth_service import AuthService
from app.core.dependency_chain import get_auth_service
from app.platform.auth.router import local_auth_router
from app.core.store import get_current_user
from app.platform.users.model.user import User

def get_jwt_key_manager(request: Request):
    return request.app.state.jwt_key_manager
router = APIRouter(prefix="/auth", tags=["Auth"])

router.include_router(local_auth_router.router)

oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url=settings.SERVER_METADATA_URL,
    client_kwargs={
        "scope": "openid email profile"
    }
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
    and sets access and refresh tokens in HTTP-only cookies.
    """
)
async def google_callback(request: Request, service: AuthService = Depends(get_auth_service), key_manager=Depends(get_jwt_key_manager)):
    token = await oauth.google.authorize_access_token(request)
    response = RedirectResponse(url="/")
    
    user_info = token.get("userinfo")
    
    tokens = service.login_with_google(user_info, key_manager)
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




@router.get(
    "/me",
    summary="Get current logged in user details",
    description="Returns user profile and role for auto-auth check."
)
def get_me(current_user: User = Depends(get_current_user)):
    role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    return {
        "uuid": str(current_user.uuid),
        "name": current_user.name,
        "email": current_user.email,
        "role": role_str
    }


@router.post(
    "/logout",
    summary="Logout user",
    description="Clears access and refresh token HttpOnly cookies."
)
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}