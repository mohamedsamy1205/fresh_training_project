<<<<<<< HEAD:app/platform/users/router/user_router.py
from fastapi import APIRouter, Depends, Query
from app.core.dependency_chain import get_user_service
from app.platform.users.service.user_service import UserService
from app.platform.users.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_current_user
from app.platform.users.models.user import User
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, current_user: User = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    return service.create_user( user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: User = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    return service.get_user( user_id)


@router.get("/", response_model=List[UserResponse])
def get_users(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
    limit: int = Query(10, le=100),
    skip: int = Query(0, ge=0),
    sort_by: str = "id",
    order: str = "asc",
):
    return service.get_users(
        limit=limit,
        skip=skip,
        sort_by=sort_by,
        order=order,
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, updates: UserUpdate,  current_user: User = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    return service.update_user(user_id, updates)


@router.delete("/{user_id}")
def delete_user(user_id: int,  current_user: User = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    return service.delete_user( user_id)
=======
from fastapi import APIRouter, Depends, Query
from app.platform.users.service.user_service import UserService
from app.platform.users.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_current_user
from app.platform.users.models.user import User
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, current_user: User = Depends(get_current_user)):
    return UserService.create_user( user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: User = Depends(get_current_user)):
    return UserService.get_user( user_id)


@router.get("/", response_model=List[UserResponse])
def get_users(
    current_user: User = Depends(get_current_user),

    limit: int = Query(10, le=100),
    skip: int = Query(0, ge=0),
    sort_by: str = "id",
    order: str = "asc",
):
    return UserService.get_users(
        limit=limit,
        skip=skip,
        sort_by=sort_by,
        order=order,
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, updates: UserUpdate,  current_user: User = Depends(get_current_user)):
    return UserService.update_user(user_id, updates)


@router.delete("/{user_id}")
def delete_user(user_id: int,  current_user: User = Depends(get_current_user)):
    return UserService.delete_user( user_id)
>>>>>>> cbe60a4 (...):app/platform/users/controller/user_controller.py
