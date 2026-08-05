import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    Enum as SqlEnum
)
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.common.enums import InvestmentRequestStatus

class InvestmentRequest(Base):
    __tablename__ = "investment_requests"

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
        nullable=False,
        index=True
    )

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.uuid"),
        nullable=False,
        index=True
    )

    wallet_id = Column(
        UUID(as_uuid=True),
        ForeignKey("wallets.uuid"),
        nullable=False,
        index=True
    )

    amount = Column(Numeric(18, 4), nullable=False)

    status = Column(
        SqlEnum(InvestmentRequestStatus, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=InvestmentRequestStatus.PENDING.value
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
