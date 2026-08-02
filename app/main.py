from fastapi import FastAPI
from app.core.database import Base, get_engine
from app.core.config import settings
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.platform.users.router import user_router
from app.platform.auth.router import auth_router
from app.business.wallet.router import wallet_router
from app.core.models_loader import *

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY  
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=get_engine())

app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(wallet_router.router)