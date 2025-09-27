import uuid

from sqlalchemy import Column, String, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.base import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=False)

    scenario = Column(String(255), nullable=False)
    status = Column(String(50))
    tags = Column(JSON, nullable=True)
    duration = Column(Float, default=0.0)
    failed_step = Column(String(255), nullable=True)
    error = Column(String, nullable=True)
    attachments = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    execution = relationship("Execution", back_populates="scenarios")
