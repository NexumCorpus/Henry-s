from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Index, DECIMAL, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class ItemCategory(str, enum.Enum):
    SPIRITS = "spirits"
    BEER = "beer"
    WINE = "wine"
    MIXERS = "mixers"
    GARNISHES = "garnishes"
    FOOD = "food"
    SUPPLIES = "supplies"


class UnitOfMeasure(str, enum.Enum):
    BOTTLE = "bottle"
    CASE = "case"
    LITER = "liter"
    GALLON = "gallon"
    OUNCE = "ounce"
    POUND = "pound"
    EACH = "each"


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(Enum(ItemCategory), nullable=False, index=True)
    barcode = Column(String(100), unique=True, index=True)
    sku = Column(String(100), index=True)
    description = Column(Text)
    unit_of_measure = Column(Enum(UnitOfMeasure), nullable=False)
    cost_per_unit = Column(DECIMAL(10, 2))
    selling_price = Column(DECIMAL(10, 2))
    par_level = Column(Float, default=0.0, nullable=False)
    reorder_point = Column(Float, default=0.0, nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), index=True)
    expiration_days = Column(Float)  # Days until expiration for perishable items
    is_active = Column(String(10), default="true", nullable=False)  # Using string to match existing schema
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    supplier = relationship("Supplier", back_populates="inventory_items")
    stock_levels = relationship("StockLevel", back_populates="item", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="item")
    notifications = relationship("Notification", back_populates="item")

    # Indexes for performance
    __table_args__ = (
        Index('idx_inventory_category_active', 'category', 'is_active'),
        Index('idx_inventory_supplier_active', 'supplier_id', 'is_active'),
    )

    def __repr__(self):
        return f"<InventoryItem(id={self.id}, name='{self.name}', category='{self.category}')>"


class StockLevel(Base):
    __tablename__ = "stock_levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False, index=True)
    current_stock = Column(Float, default=0.0, nullable=False)
    reserved_stock = Column(Float, default=0.0, nullable=False)  # Stock reserved for pending orders
    last_counted = Column(DateTime(timezone=True))
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    item = relationship("InventoryItem", back_populates="stock_levels")
    location = relationship("Location", back_populates="stock_levels")

    # Unique constraint to ensure one stock level per item-location combination
    __table_args__ = (
        Index('idx_stock_item_location', 'item_id', 'location_id', unique=True),
        Index('idx_stock_location_updated', 'location_id', 'last_updated'),
    )

    def __repr__(self):
        return f"<StockLevel(item_id={self.item_id}, location_id={self.location_id}, stock={self.current_stock})>"