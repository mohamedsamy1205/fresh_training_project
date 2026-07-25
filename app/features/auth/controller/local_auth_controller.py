from fastapi import Request, HTTPException, APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/refresh")
def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

    except:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token({"sub": user_id})

    return {"access_token": new_access_token}