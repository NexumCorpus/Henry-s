from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.services.inventory import InventoryService
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    InventoryItemWithStock,
    StockLevelCreate,
    StockLevelUpdate,
    StockLevelResponse
)
from app.schemas.user import UserResponse
from app.models.transaction import TransactionType

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/items", response_model=List[InventoryItemResponse])
async def get_inventory_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    active_only: bool = Query(True, description="Show only active items"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get inventory items with optional filtering"""
    service = InventoryService(db)
    return service.get_items(skip, limit, category, location_id, active_only)


@router.get("/items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific inventory item by ID"""
    service = InventoryService(db)
    item = service.get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    return item


@router.post("/items", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item_data: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new inventory item"""
    # Check if user has permission to create items (manager or admin)
    if current_user.role not in ["manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create inventory items"
        )
    
    service = InventoryService(db)
    
    # Check if barcode already exists
    if item_data.barcode:
        existing_item = service.get_item_by_barcode(item_data.barcode)
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item with this barcode already exists"
            )
    
    return service.create_item(item_data)


@router.put("/items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: UUID,
    item_data: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update an existing inventory item"""
    # Check if user has permission to update items (manager or admin)
    if current_user.role not in ["manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update inventory items"
        )
    
    service = InventoryService(db)
    
    # Check if barcode conflicts with another item
    if item_data.barcode:
        existing_item = service.get_item_by_barcode(item_data.barcode)
        if existing_item and existing_item.id != item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another item with this barcode already exists"
            )
    
    updated_item = service.update_item(item_id, item_data)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    return updated_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete an inventory item (soft delete)"""
    # Only admins can delete items
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete inventory items"
        )
    
    service = InventoryService(db)
    success = service.delete_item(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )


@router.get("/items/search", response_model=List[InventoryItemResponse])
async def search_inventory_items(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Search inventory items by name, barcode, or SKU"""
    service = InventoryService(db)
    return service.search_items(q, limit)


@router.post("/scan", response_model=dict)
async def scan_barcode(
    barcode: str = Query(..., description="Barcode to scan"),
    location_id: Optional[UUID] = Query(None, description="Location context for stock info"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Scan barcode and return item information with stock levels"""
    service = InventoryService(db)
    result = service.scan_barcode(barcode, location_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result


@router.get("/stock/location/{location_id}", response_model=List[StockLevelResponse])
async def get_stock_by_location(
    location_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all stock levels for a specific location"""
    service = InventoryService(db)
    return service.get_stock_levels_by_location(location_id)


@router.get("/stock/item/{item_id}", response_model=List[StockLevelResponse])
async def get_stock_by_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get stock levels for an item across all locations"""
    service = InventoryService(db)
    return service.get_stock_levels_by_item(item_id)


@router.get("/stock/{item_id}/{location_id}", response_model=StockLevelResponse)
async def get_stock_level(
    item_id: UUID,
    location_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get stock level for specific item at specific location"""
    service = InventoryService(db)
    stock = service.get_stock_level(item_id, location_id)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock level not found for this item and location"
        )
    return stock


@router.put("/stock/{item_id}/{location_id}", response_model=StockLevelResponse)
async def update_stock_level(
    item_id: UUID,
    location_id: UUID,
    stock_data: StockLevelCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Update stock level for item at location"""
    # Check if user has permission to update stock (bartender, manager, or admin)
    if current_user.role not in ["bartender", "manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update stock levels"
        )
    
    service = InventoryService(db)
    return service.update_stock_level(item_id, location_id, stock_data)


@router.post("/adjust/{item_id}/{location_id}", response_model=StockLevelResponse)
async def adjust_stock(
    item_id: UUID,
    location_id: UUID,
    quantity_change: float = Query(..., description="Quantity to add (positive) or remove (negative)"),
    transaction_type: TransactionType = Query(TransactionType.ADJUSTMENT, description="Type of adjustment"),
    notes: Optional[str] = Query(None, description="Notes about the adjustment"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Adjust stock level with audit logging"""
    # All authenticated users can make adjustments, but with different transaction types
    service = InventoryService(db)
    
    # Verify item and location exist
    item = service.get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    stock = service.adjust_stock(
        item_id, 
        location_id, 
        quantity_change, 
        current_user.id, 
        transaction_type, 
        notes
    )
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock level not found for this item and location"
        )
    
    return stock


@router.get("/alerts/low-stock", response_model=List[dict])
async def get_low_stock_alerts(
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get items with stock levels below reorder point"""
    service = InventoryService(db)
    return service.get_low_stock_items(location_id)