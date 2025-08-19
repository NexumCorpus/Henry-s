from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.models.inventory import ItemCategory, UnitOfMeasure


class InventoryItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: ItemCategory
    barcode: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit_of_measure: UnitOfMeasure
    cost_per_unit: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    selling_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    par_level: float = Field(0.0, ge=0)
    reorder_point: float = Field(0.0, ge=0)
    expiration_days: Optional[float] = Field(None, ge=0)
    is_active: str = "true"


class InventoryItemCreate(InventoryItemBase):
    supplier_id: Optional[UUID] = None


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[ItemCategory] = None
    barcode: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit_of_measure: Optional[UnitOfMeasure] = None
    cost_per_unit: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    selling_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    par_level: Optional[float] = Field(None, ge=0)
    reorder_point: Optional[float] = Field(None, ge=0)
    supplier_id: Optional[UUID] = None
    expiration_days: Optional[float] = Field(None, ge=0)
    is_active: Optional[str] = None


class InventoryItemResponse(InventoryItemBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    supplier_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class StockLevelBase(BaseModel):
    current_stock: float = Field(0.0, ge=0)
    reserved_stock: float = Field(0.0, ge=0)
    last_counted: Optional[datetime] = None


class StockLevelCreate(StockLevelBase):
    item_id: UUID
    location_id: UUID


class StockLevelUpdate(BaseModel):
    current_stock: Optional[float] = Field(None, ge=0)
    reserved_stock: Optional[float] = Field(None, ge=0)
    last_counted: Optional[datetime] = None


class StockLevelResponse(StockLevelBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_id: UUID
    location_id: UUID
    last_updated: datetime


class InventoryItemWithStock(InventoryItemResponse):
    stock_levels: list[StockLevelResponse] = []