from sqlalchemy.orm import Session
from app.features.users.repository.user_repository import UserRepository
from app.features.users.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:

    @staticmethod
    def create_user(db: Session, user: UserCreate):
        existing = UserRepository.get_by_email(db, user.email)
        if existing:
            raise Exception("Email already exists")

        hashed_password = None
        if user.password:
            hashed_password = pwd_context.hash(user.password)

        return UserRepository.create(db, {
            "name": user.name,
            "email": user.email,
            "hashed_password": hashed_password,
            "age": user.age,
            "provider": "local"
        })

    @staticmethod
    def get_user(db: Session, user_id: int):
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise Exception("User not found")
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, updates: UserUpdate):
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise Exception("User not found")

        return UserRepository.update(db, user, updates.dict(exclude_unset=True))

    @staticmethod
    def delete_user(db: Session, user_id: int):
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise Exception("User not found")

        UserRepository.delete(db, user)
        return {"message": "User deleted"}