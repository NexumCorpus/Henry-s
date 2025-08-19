from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.location import LocationType


class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: LocationType
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[LocationType] = None
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime