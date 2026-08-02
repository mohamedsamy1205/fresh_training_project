import uuid

from sqlalchemy import (
    Column,
    Numeric,
    Integer,
    String,
    ForeignKey,
    DateTime
)

from sqlalchemy.dialects.postgresql import UUID

from datetime import datetime

from app.core.database import Base


class Wallet(Base):

    __tablename__ = "wallets"


    id = Column(Integer, primary_key=True, index=True)

    uuid = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=False
    )


    balance = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    name = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )