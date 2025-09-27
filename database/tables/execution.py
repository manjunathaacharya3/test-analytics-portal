import uuid

from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.base import Base


# Add the back_populates in Execution
class Execution(Base):
    __tablename__ = "executions"
    # ... existing columns ...
    scenarios = relationship("Scenario", back_populates="execution")

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=False)

    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    total = Column(Integer, default=0)  # ✅ Add this
    duration = Column(Float, default=0.0)
    status = Column(String(50), nullable=False)

    # raw_report = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    module = relationship("Module", back_populates="executions")
