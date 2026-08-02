<<<<<<< HEAD:app/platform/auth/router/auth_router.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.platform.auth.service.auth_service import AuthService
from app.core.dependency_chain import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

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


# 🔥 1. redirect to google
@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


# 🔥 2. callback
@router.get("/google/callback")
async def google_callback(request: Request, service: AuthService = Depends(get_auth_service)):
    token = await oauth.google.authorize_access_token(request)
    response = RedirectResponse(url="http://localhost:8000/docs")
    

    user_info = token.get("userinfo")
    
    tokens = service.login_with_google( user_info)
    access_value = tokens["access_token"]
    refresh_value = tokens["refresh_token"]
    response.set_cookie(
            key="access_token",
            value= access_value,
            httponly=True,
            secure=False,  
            samesite="lax"
        )
    response.set_cookie(
                key="refresh_token",
                value= refresh_value,
                httponly=True,
                secure=False,  
                samesite="lax"
            )

=======
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.platform.auth.service.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

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


# 🔥 1. redirect to google
@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


# 🔥 2. callback
@router.get("/google/callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    response = RedirectResponse(url="https://www.google.com/")
    

    user_info = token.get("userinfo")
    
    service = AuthService.login_with_google( user_info)
    access_value = service["access_token"]
    refresh_value = service["refresh_token"]
    response.set_cookie(
            key="access_token",
            value= access_value,
            httponly=True,
            secure=False,  
            samesite="lax"
        )
    response.set_cookie(
                key="refresh_token",
                value= refresh_value,
                httponly=True,
                secure=False,  
                samesite="lax"
            )

>>>>>>> cbe60a4 (...):app/platform/auth/controller/auth_controller.py
    return response