import uuid
import enum 
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Boolean, Enum as SqlEnum
from app.core.database import Base
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.common.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    uuid = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=True,
        index=True
    )

    name = Column(String, nullable=False)

    email = Column(String, unique=True, index=True, nullable=False)

    phone_number = Column(String, nullable=True)

    provider = Column(String, nullable=True)

    hashed_password = Column(String, nullable=True)  

    role = Column(
        SqlEnum(UserRole, values_callable=lambda enum: [e.value for e in enum]),
        nullable=True,
        default=UserRole.INVESTOR.value
    )

    age = Column(Integer, nullable=True)

    is_pending = Column(Boolean, default=True)

    is_locked = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())