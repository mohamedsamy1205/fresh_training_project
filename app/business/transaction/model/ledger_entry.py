import uuid
from sqlalchemy import (
    Column,
    Numeric,
    Integer,
    ForeignKey,
    DateTime,
    Enum as SqlEnum
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base
from app.common.enums import LedgerEntryType

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)

    uuid = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )

    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.uuid"),
        nullable=False,
        index=True
    )

    wallet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wallets.uuid"),
        nullable=False,
        index=True
    )

    entry_type = Column(
        SqlEnum(LedgerEntryType, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False
    )

    amount = Column(Numeric(18, 4), nullable=False)

    balance_after = Column(Numeric(18, 4), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
