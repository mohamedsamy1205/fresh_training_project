from fastapi import FastAPI
from app.core.database import Base, get_engine
from app.core.config import settings
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.platform.users.router import user_router
from app.platform.auth.router import auth_router
from app.business.wallet.router import wallet_router
from app.business.transaction.router import transaction_router
from app.business.mony_movements.router import mony_movements_router
from app.business.projects.router import project_router
from app.core.exception_handlers import register_exception_handlers
from app.core.models_loader import *
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.redis import redis_client


app = FastAPI()

# # redis check
# @app.on_event("startup")
# async def startup():
#     ok = await redis_client.ping()
#     if not ok:
#         raise Exception("ERROR:      Redis is not connected")
#     print("INFO:     Redis connected.") # TODO: replace this with structured logging

#=================================================================================================================================

# Register global exception handlers
register_exception_handlers(app)

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

app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(wallet_router.router)
app.include_router(transaction_router.router)
app.include_router(mony_movements_router.router)
app.include_router(project_router.router)


if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def serve_index():
    if os.path.exists("templates/index.html"):
        return FileResponse("templates/index.html")
    return {"message": "System active"}

@app.get("/admin", include_in_schema=False)
def serve_admin():
    if os.path.exists("templates/admin.html"):
        return FileResponse("templates/admin.html")
    return {"message": "Admin dashboard"}

@app.get("/investor", include_in_schema=False)
def serve_investor():
    if os.path.exists("templates/investor.html"):
        return FileResponse("templates/investor.html")
    return {"message": "Investor dashboard"}



