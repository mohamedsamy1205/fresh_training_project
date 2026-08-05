import uuid
from sqlalchemy import (
    Column,
    Numeric,
    Enum as SqlEnum,
    Integer,
    String,
    ForeignKey,
    DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base
from app.common.enums import TransactionType, TransactionStatus

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    uuid = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )

    idempotency_key = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=True
    )

    wallet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wallets.uuid"),
        nullable=False,
        index=True
    )

    amount = Column(Numeric(18, 4), nullable=False)

    currency = Column(String(3), nullable=False, default="USD")

    type = Column(
        SqlEnum(TransactionType, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False
    )

    status = Column(
        SqlEnum(TransactionStatus, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=TransactionStatus.PENDING.value
    )

    description = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)