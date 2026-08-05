from sqlalchemy import (
    Column,
    Numeric,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Enum as SqlEnum,
    CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base
from app.common.enums import WalletType
import uuid

class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="cw_wallet_balance_non_negative"),
    )

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
        nullable=True
    )


    currency = Column(
        String(3),
        nullable=False,
        default="USD"
    )

    balance = Column(
        Numeric(18, 4),
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