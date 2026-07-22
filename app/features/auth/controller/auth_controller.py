from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from app.core.database import get_db
from app.features.auth.service.auth_service import AuthService

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
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)

    user_info = token.get("userinfo")

    return AuthService.login_with_google(db, user_info)