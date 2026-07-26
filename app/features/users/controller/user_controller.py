from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.features.users.service.user_service import UserService
from app.features.users.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_current_user
from app.features.users.models.user import User
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return UserService.create_user(db, user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return UserService.get_user(db, user_id)


@router.get("/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),

    limit: int = Query(10, le=100),
    skip: int = Query(0, ge=0),
    sort_by: str = "id",
    order: str = "asc",
):
    return UserService.get_users(
        db=db,
        limit=limit,
        skip=skip,
        sort_by=sort_by,
        order=order,
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, updates: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return UserService.update_user(db, user_id, updates)


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return UserService.delete_user(db, user_id)