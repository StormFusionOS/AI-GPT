"""SQLAlchemy model for CRM contacts used in API integration tests."""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, func

from .base import Base


class Contact(Base):
    """Light-weight contact model aligning with the initial migration."""

    __tablename__ = 'contacts'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Contact id={self.id!r} name={self.name!r}>"
