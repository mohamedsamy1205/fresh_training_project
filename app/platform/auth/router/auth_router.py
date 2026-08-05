from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from app.platform.auth.service.auth_service import AuthService
from app.core.dependency_chain import get_auth_service
from app.platform.auth.router import local_auth_router

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
async def google_callback(request: Request, service: AuthService = Depends(get_auth_service)):
    token = await oauth.google.authorize_access_token(request)
    response = RedirectResponse(url="http://localhost:8000/docs")
    

    user_info = token.get("userinfo")
    
    tokens = service.login_with_google(user_info)
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