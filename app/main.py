from fastapi import FastAPI
from app.core.database import Base, engine
from app.core.config import settings
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.features.users.controller import user_controller
from app.features.auth.controller import auth_controller

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

Base.metadata.create_all(bind=engine)

app.include_router(user_controller.router)
app.include_router(auth_controller.router)