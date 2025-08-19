from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    api_endpoint: Optional[str] = Field(None, max_length=500)
    payment_terms: Optional[str] = Field(None, max_length=100)
    delivery_schedule: Optional[str] = Field(None, max_length=255)
    minimum_order_amount: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    is_preferred: bool = False


class SupplierCreate(SupplierBase):
    api_credentials: Optional[Dict[str, Any]] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_credentials: Optional[Dict[str, Any]] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    delivery_schedule: Optional[str] = Field(None, max_length=255)
    minimum_order_amount: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_preferred: Optional[bool] = None


class SupplierResponse(SupplierBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime