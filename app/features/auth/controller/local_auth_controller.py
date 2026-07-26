from fastapi import Request, HTTPException, APIRouter
from app.features.auth.service.auth_service from refresh_token
router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/refresh")
def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    return refresh_token(refresh_token)