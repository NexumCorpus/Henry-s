from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    quantity: float = Field(..., ne=0)  # Cannot be zero
    unit_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    total_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    pos_transaction_id: Optional[str] = Field(None, max_length=100)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class TransactionCreate(TransactionBase):
    item_id: UUID
    location_id: UUID
    transaction_type: TransactionType


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    item_id: UUID
    location_id: UUID
    user_id: UUID
    transaction_type: TransactionType
    timestamp: datetime


class TransactionWithDetails(TransactionResponse):
    item_name: Optional[str] = None
    location_name: Optional[str] = None
    user_name: Optional[str] = None