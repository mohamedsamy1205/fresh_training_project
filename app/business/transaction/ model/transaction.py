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

    wallet_id = Column(UUID, ForeignKey("wallets.id"))

    amount = Column(Float, nullable=False)

    type = Column(Enum(TransactionType))

    status = Column(Enum(TransactionStatus)) 

    description = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)