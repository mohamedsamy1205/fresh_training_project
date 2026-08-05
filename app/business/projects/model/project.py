import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Enum as SqlEnum
)
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.common.enums import ProjectStatus

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    uuid = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(String, nullable=False)

    start_date = Column(DateTime, nullable=False)

    end_date = Column(DateTime, nullable=False)

    initial_amount = Column(
        Numeric(18, 4),
        nullable=False,
        default=0
    )

    final_amount = Column(
        Numeric(18, 4),
        nullable=True
    )

    status = Column(
        SqlEnum(ProjectStatus, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        default=ProjectStatus.ACTIVE.value
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
