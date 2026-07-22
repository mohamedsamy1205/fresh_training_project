from fastapi import FastAPI
from app.core.database import Base, engine
from app.core.config import settings
from starlette.middleware.sessions import SessionMiddleware
# ✅ imports صح
from app.features.users.controller import user_controller
from app.features.auth.controller import auth_controller

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY  
)
Base.metadata.create_all(bind=engine)

# ✅ include routers صح
app.include_router(user_controller.router)
app.include_router(auth_controller.router)