from fastapi import Request, HTTPException, APIRouter
from app.platform.auth.service.auth_service import AuthService
from app.core.dependency_chain import get_auth_service


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/refresh")
def refresh(request: Request, service: AuthService = Depends(get_auth_service)):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    return service.refresh_token(refresh_token)