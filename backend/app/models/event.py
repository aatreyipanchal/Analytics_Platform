from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, index=True, nullable=False)
    source = Column(String, default="api", nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    user_id = Column(String, index=True)
    properties = Column(JSONB, nullable=False, default=dict)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="events")
