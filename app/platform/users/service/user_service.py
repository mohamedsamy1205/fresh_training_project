from sqlalchemy.orm import Session
from app.platform.users.repository.user_repository import UserRepository
from app.platform.users.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:

    @staticmethod
    def create_user( user: UserCreate):
        existing = UserRepository.get_by_email( user.email)
        if existing:
            raise Exception("Email already exists")

        hashed_password = None
        if user.password:
            hashed_password = pwd_context.hash(user.password)

        return UserRepository.create( {
            "name": user.name,
            "email": user.email,
            "hashed_password": hashed_password,
            "age": user.age,
            "provider": "local"
        })

    @staticmethod
    def get_user( user_id: int):
        user = UserRepository.get_by_id( user_id)
        if not user:
            raise Exception("User not found")
        return user

    @staticmethod
    def get_users(limit, skip, sort_by, order):
        user = UserRepository.get_users( limit, skip, sort_by, order, )
        if not user:
            raise Exception("User not found")
        return user

    @staticmethod
    def update_user( user_id: int, updates: UserUpdate):
        user = UserRepository.get_by_id( user_id)
        if not user:
            raise Exception("User not found")

        return UserRepository.update( user, updates.dict(exclude_unset=True))

    @staticmethod
    def delete_user( user_id: int):
        user = UserRepository.get_by_id( user_id)
        if not user:
            raise Exception("User not found")

        UserRepository.delete( user)
        return {"message": "User deleted"}

