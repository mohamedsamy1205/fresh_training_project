from pathlib import Path

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
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.redis import redis_client as redis
from contextlib import asynccontextmanager
from app.core.jwt_key_manager import JWTKeyManager
from app.core.telemetry import setup_telemetry
import logging
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Create JWT key manager
    key_manager = JWTKeyManager(redis)

    # Generate NEW RSA key pair
    await key_manager.initialize()

    # Make it available throughout the application
    app.state.jwt_key_manager = key_manager

    yield

    # Cleanup
    await redis.close()




app = FastAPI(
    lifespan=lifespan,
    title="Fresh Prioject API",
    version="1.0.0",
    # docs_url=None,
    # redoc_url=None,
)

# # redis check
# @app.on_event("startup")
# async def startup():
#     ok = await redis_client.ping()
#     if not ok:
#         raise Exception("ERROR:      Redis is not connected")
#     print("INFO:     Redis connected.") # TODO: replace this with structured logging

#=================================================================================================================================

# Register global exception handlers
setup_telemetry(app) 
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

FastAPIInstrumentor.instrument_app(
    app,
    exclude_spans=["send", "receive"]
)

app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(wallet_router.router)
app.include_router(transaction_router.router)
app.include_router(mony_movements_router.router)
app.include_router(project_router.router)


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

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



# @app.get("/docs", include_in_schema=False)
# async def custom_swagger():
#     return HTMLResponse(
#         """
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <title>Fresh Prioject API</title>

#             <link
#                 rel="stylesheet"
#                 type="text/css"
#                 href="/static/swagger/custom.css"
#             >

#             <link
#                 rel="stylesheet"
#                 type="text/css"
#                 href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css"
#             >
#         </head>

#         <body>
#             <div id="swagger-ui"></div>

#             <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>

#             <script>
#                 window.onload = function () {
#                     SwaggerUIBundle({
#                         url: "/openapi.json",
#                         dom_id: "#swagger-ui",
#                         deepLinking: true,
#                         persistAuthorization: true,
#                         displayRequestDuration: true,
#                         filter: true,
#                         tryItOutEnabled: true
#                     });
#                 };
#             </script>
#         </body>
#         </html>
#         """
#     )