from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class LocationType(str, enum.Enum):
    BAR = "bar"
    STORAGE = "storage"
    KITCHEN = "kitchen"
    ROOFTOP = "rooftop"


class Location(Base):
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False, index=True)
    type = Column(Enum(LocationType), nullable=False)
    description = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    stock_levels = relationship("StockLevel", back_populates="location")
    transactions = relationship("Transaction", back_populates="location")
    notification_rules = relationship("NotificationRule", back_populates="location")
    notifications = relationship("Notification", back_populates="location")

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}', type='{self.type}')>"