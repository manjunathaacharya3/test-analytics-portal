import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    repository_url = Column(String(500), nullable=True)
    owner = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # 🔹 Relationship: One project → Many modules
    modules = relationship(
        "Module",  # reference to Module class (defined later)
        back_populates="project",  # keeps bidirectional access
        cascade="all, delete-orphan"  # deletes modules if project is deleted
    )
