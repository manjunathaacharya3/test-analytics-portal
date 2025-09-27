import uuid

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.base import Base


class Module(Base):
    __tablename__ = "modules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # 🔹 Relationships
    project = relationship(
        "Project",
        back_populates="modules",  # ✅ matches Project.modules
        lazy="joined"  # auto-joins project when fetching a module
    )

    executions = relationship(
        "Execution",
        back_populates="module",  # ✅ will match Execution.module
        cascade="all, delete-orphan"
    )
