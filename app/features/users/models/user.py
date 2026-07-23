from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base
from sqlalchemy.sql import func
from sqlalchemy import DateTime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(String, unique=True, index=True, nullable=False)

    phone_number = Column(String, nullable=True)

    provider = Column(String, nullable=True)

    hashed_password = Column(String, nullable=True)  

    age = Column(Integer, nullable=True)

    is_pending = Column(Boolean, default=True)

    is_locked = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())