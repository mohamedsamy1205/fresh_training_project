<<<<<<< HEAD
from sqlalchemy.orm import Session
from app.platform.users.repository.user_repository import UserRepository
from app.platform.users.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def create_user(self, user: UserCreate):
        existing = self.repo.get_by_email(user.email)
        if existing:
            raise Exception("Email already exists")

        hashed_password = None
        if user.password:
            hashed_password = pwd_context.hash(user.password)

        return self.repo.create({
            "name": user.name,
            "email": user.email,
            "hashed_password": hashed_password,
            "age": user.age,
            "provider": "local"
        })

    def create_google_user(self, name: str, email: str):
        existing = self.repo.get_by_email(email)
        if existing:
            return existing

        return self.repo.create({
            "name": name,
            "email": email,
            "hashed_password": None,
            "age": None,
            "provider": "google"
        })

    def get_user(self, user_id: int):
        user = self.repo.get_by_id(user_id)
        if not user:
            raise Exception("User not found")
        return user

    def get_by_email(self, user_email: str):
        return self.repo.get_by_email(user_email)  # 👈 هنعدل دي كمان تحت

    def get_users(self, limit, skip, sort_by, order):
        return self.repo.get_users(limit, skip, sort_by, order)

    def update_user(self, user_id: int, updates: UserUpdate):
        user = self.repo.get_by_id(user_id)
        if not user:
            raise Exception("User not found")

        return self.repo.update(user, updates.dict(exclude_unset=True))

    def delete_user(self, user_id: int):
        user = self.repo.get_by_id(user_id)
        if not user:
            raise Exception("User not found")

        self.repo.delete(user)
        return {"message": "User deleted"}
=======
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

>>>>>>> cbe60a4 (...)
