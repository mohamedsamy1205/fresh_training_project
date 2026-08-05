import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    DateTime,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Investment(Base):
    __tablename__ = "investments"

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

    created_at = Column(DateTime, default=datetime.utcnow)
