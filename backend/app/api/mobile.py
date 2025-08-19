from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from typing import List, Optional, Dict, Any, Set
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.services.inventory import InventoryService
from app.services.barcode import BarcodeService
from app.services.websocket import inventory_ws_service
from app.schemas.inventory import StockLevelResponse
from app.schemas.user import UserResponse
from app.models.transaction import TransactionType
from pydantic import BaseModel
import base64
import asyncio


router = APIRouter(prefix="/mobile", tags=["mobile"])


class BarcodeImageScan(BaseModel):
    """Schema for barcode scanning with base64 image"""
    image_data: str
    location_id: Optional[UUID] = None
    format: str = "base64"  # Currently only base64 supported


class QuickStockUpdate(BaseModel):
    """Schema for quick stock updates from mobile"""
    item_id: UUID
    location_id: UUID
    new_stock: float
    transaction_type: TransactionType = TransactionType.ADJUSTMENT
    notes: Optional[str] = None


class BulkStockUpdate(BaseModel):
    """Schema for bulk stock updates"""
    updates: List[QuickStockUpdate]


class OfflineTransaction(BaseModel):
    """Schema for offline transactions to sync"""
    local_id: str
    item_id: UUID
    location_id: UUID
    quantity_change: float
    transaction_type: TransactionType
    timestamp: float
    notes: Optional[str] = None


class OfflineSyncRequest(BaseModel):
    """Schema for offline sync request"""
    transactions: List[OfflineTransaction]
    last_sync_timestamp: Optional[float] = None


@router.post("/scan/barcode", response_model=Dict[str, Any])
async def scan_barcode_image(
    scan_request: BarcodeImageScan,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Scan barcode from uploaded image data (mobile optimized)"""
    barcode_service = BarcodeService(db)
    
    result = barcode_service.scan_barcode_from_base64(
        scan_request.image_data, 
        scan_request.location_id
    )
    
    # Send result via WebSocket for real-time updates
    await inventory_ws_service.handle_barcode_scan_result(
        str(current_user.id), 
        result
    )
    
    return result


@router.post("/scan/barcode/file")
async def scan_barcode_file(
    file: UploadFile = File(...),
    location_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Scan barcode from uploaded file (alternative to base64)"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    try:
        # Read file and convert to base64
        file_content = await file.read()
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        barcode_service = BarcodeService(db)
        result = barcode_service.scan_barcode_from_base64(base64_image, location_id)
        
        # Send result via WebSocket
        await inventory_ws_service.handle_barcode_scan_result(
            str(current_user.id), 
            result
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )


@router.get("/stock/quick/{location_id}", response_model=List[Dict[str, Any]])
async def get_quick_stock_overview(
    location_id: UUID,
    category: Optional[str] = Query(None, description="Filter by category"),
    low_stock_only: bool = Query(False, description="Show only low stock items"),
    limit: int = Query(50, ge=1, le=200, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get quick stock overview optimized for mobile display"""
    service = InventoryService(db)
    
    # Get stock levels for location
    stock_levels = service.get_stock_levels_by_location(location_id)
    
    # Filter and format for mobile
    mobile_stock = []
    for stock in stock_levels[:limit]:
        item = service.get_item(stock.item_id)
        if not item:
            continue
            
        # Apply category filter
        if category and item.category != category:
            continue
            
        # Apply low stock filter
        is_low_stock = stock.current_stock <= item.reorder_point
        if low_stock_only and not is_low_stock:
            continue
        
        mobile_stock.append({
            "item_id": str(item.id),
            "name": item.name,
            "category": item.category,
            "current_stock": stock.current_stock,
            "unit_of_measure": item.unit_of_measure,
            "reorder_point": item.reorder_point,
            "par_level": item.par_level,
            "is_low_stock": is_low_stock,
            "last_updated": stock.last_updated.isoformat(),
            "barcode": item.barcode
        })
    
    return mobile_stock


@router.post("/stock/quick-update", response_model=Dict[str, Any])
async def quick_stock_update(
    update: QuickStockUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Quick stock update optimized for mobile (single item)"""
    service = InventoryService(db)
    
    # Get current stock level
    current_stock_level = service.get_stock_level(update.item_id, update.location_id)
    old_stock = current_stock_level.current_stock if current_stock_level else 0.0
    
    # Calculate quantity change
    quantity_change = update.new_stock - old_stock
    
    # Update stock
    updated_stock = service.adjust_stock(
        update.item_id,
        update.location_id,
        quantity_change,
        current_user.id,
        update.transaction_type,
        update.notes
    )
    
    if not updated_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item or location not found"
        )
    
    # Send real-time update via WebSocket
    await inventory_ws_service.handle_inventory_update(
        update.item_id,
        update.location_id,
        old_stock,
        update.new_stock,
        str(current_user.id),
        update.transaction_type.value
    )
    
    # Check for low stock alert
    item = service.get_item(update.item_id)
    if item and update.new_stock <= item.reorder_point:
        await inventory_ws_service.handle_low_stock_alert(
            update.item_id,
            update.location_id,
            update.new_stock,
            item.reorder_point,
            item.name
        )
    
    return {
        "success": True,
        "item_id": str(update.item_id),
        "location_id": str(update.location_id),
        "old_stock": old_stock,
        "new_stock": update.new_stock,
        "change": quantity_change,
        "updated_at": updated_stock.last_updated.isoformat()
    }


@router.post("/stock/bulk-update", response_model=Dict[str, Any])
async def bulk_stock_update(
    bulk_update: BulkStockUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Bulk stock update for multiple items (mobile optimized)"""
    service = InventoryService(db)
    
    successful_updates = []
    failed_updates = []
    
    for update in bulk_update.updates:
        try:
            # Get current stock level
            current_stock_level = service.get_stock_level(update.item_id, update.location_id)
            old_stock = current_stock_level.current_stock if current_stock_level else 0.0
            
            # Calculate quantity change
            quantity_change = update.new_stock - old_stock
            
            # Update stock
            updated_stock = service.adjust_stock(
                update.item_id,
                update.location_id,
                quantity_change,
                current_user.id,
                update.transaction_type,
                update.notes
            )
            
            if updated_stock:
                successful_updates.append({
                    "item_id": str(update.item_id),
                    "location_id": str(update.location_id),
                    "old_stock": old_stock,
                    "new_stock": update.new_stock,
                    "change": quantity_change
                })
                
                # Send real-time update via WebSocket
                await inventory_ws_service.handle_inventory_update(
                    update.item_id,
                    update.location_id,
                    old_stock,
                    update.new_stock,
                    str(current_user.id),
                    update.transaction_type.value
                )
                
                # Check for low stock alert
                item = service.get_item(update.item_id)
                if item and update.new_stock <= item.reorder_point:
                    await inventory_ws_service.handle_low_stock_alert(
                        update.item_id,
                        update.location_id,
                        update.new_stock,
                        item.reorder_point,
                        item.name
                    )
            else:
                failed_updates.append({
                    "item_id": str(update.item_id),
                    "location_id": str(update.location_id),
                    "error": "Item or location not found"
                })
                
        except Exception as e:
            failed_updates.append({
                "item_id": str(update.item_id),
                "location_id": str(update.location_id),
                "error": str(e)
            })
    
    return {
        "success": len(failed_updates) == 0,
        "successful_updates": len(successful_updates),
        "failed_updates": len(failed_updates),
        "details": {
            "successful": successful_updates,
            "failed": failed_updates
        }
    }


@router.post("/sync/offline", response_model=Dict[str, Any])
async def sync_offline_transactions(
    sync_request: OfflineSyncRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Sync offline transactions from mobile app"""
    service = InventoryService(db)
    
    processed_transactions = []
    failed_transactions = []
    
    for transaction in sync_request.transactions:
        try:
            # Update stock based on offline transaction
            updated_stock = service.adjust_stock(
                transaction.item_id,
                transaction.location_id,
                transaction.quantity_change,
                current_user.id,
                transaction.transaction_type,
                f"Offline sync: {transaction.notes or ''}"
            )
            
            if updated_stock:
                processed_transactions.append({
                    "local_id": transaction.local_id,
                    "item_id": str(transaction.item_id),
                    "location_id": str(transaction.location_id),
                    "quantity_change": transaction.quantity_change,
                    "status": "processed",
                    "server_timestamp": updated_stock.last_updated.isoformat()
                })
                
                # Send real-time update via WebSocket
                current_stock = updated_stock.current_stock
                old_stock = current_stock - transaction.quantity_change
                
                await inventory_ws_service.handle_inventory_update(
                    transaction.item_id,
                    transaction.location_id,
                    old_stock,
                    current_stock,
                    str(current_user.id),
                    transaction.transaction_type.value
                )
            else:
                failed_transactions.append({
                    "local_id": transaction.local_id,
                    "error": "Item or location not found",
                    "status": "failed"
                })
                
        except Exception as e:
            failed_transactions.append({
                "local_id": transaction.local_id,
                "error": str(e),
                "status": "failed"
            })
    
    # Send sync result via WebSocket
    await inventory_ws_service.handle_offline_sync(
        str(current_user.id),
        sync_request.transactions
    )
    
    return {
        "success": len(failed_transactions) == 0,
        "sync_timestamp": asyncio.get_event_loop().time(),
        "processed_count": len(processed_transactions),
        "failed_count": len(failed_transactions),
        "transactions": {
            "processed": processed_transactions,
            "failed": failed_transactions
        }
    }


@router.get("/categories", response_model=List[str])
async def get_categories_mobile(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all available item categories (mobile optimized)"""
    from app.models.inventory import ItemCategory
    return [category.value for category in ItemCategory]


@router.get("/locations/{location_id}/alerts", response_model=List[Dict[str, Any]])
async def get_location_alerts(
    location_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get alerts for a specific location (mobile optimized)"""
    service = InventoryService(db)
    
    # Get low stock items
    low_stock_items = service.get_low_stock_items(location_id)
    
    alerts = []
    for item_data in low_stock_items:
        alerts.append({
            "type": "low_stock",
            "severity": "critical" if item_data["current_stock"] <= 0 else "warning",
            "item_id": item_data["item_id"],
            "item_name": item_data["item_name"],
            "current_stock": item_data["current_stock"],
            "reorder_point": item_data["reorder_point"],
            "location_id": str(location_id),
            "message": f"{item_data['item_name']} is {'out of stock' if item_data['current_stock'] <= 0 else 'low on stock'}"
        })
    
    return alerts