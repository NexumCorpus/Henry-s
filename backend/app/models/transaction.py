from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Index, DECIMAL, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class TransactionType(str, enum.Enum):
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    RECEIVE = "receive"
    WASTE = "waste"
    TRANSFER = "transfer"
    COUNT = "count"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit_cost = Column(DECIMAL(10, 2))
    total_cost = Column(DECIMAL(10, 2))
    pos_transaction_id = Column(String(100), index=True)  # Reference to POS system transaction
    reference_number = Column(String(100))  # Invoice number, order number, etc.
    notes = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    item = relationship("InventoryItem", back_populates="transactions")
    location = relationship("Location", back_populates="transactions")
    user = relationship("User", back_populates="transactions")

    # Indexes for performance
    __table_args__ = (
        Index('idx_transaction_item_date', 'item_id', 'timestamp'),
        Index('idx_transaction_location_date', 'location_id', 'timestamp'),
        Index('idx_transaction_type_date', 'transaction_type', 'timestamp'),
        Index('idx_transaction_user_date', 'user_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.transaction_type}', quantity={self.quantity})>"