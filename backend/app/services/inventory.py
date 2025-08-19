from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.inventory import InventoryRepository
from app.schemas.inventory import (
    InventoryItemCreate, 
    InventoryItemUpdate, 
    InventoryItemResponse,
    StockLevelCreate,
    StockLevelUpdate,
    StockLevelResponse
)
from app.models.transaction import TransactionType
from app.core.cache import get_redis_client
import json
from datetime import datetime, timedelta


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = InventoryRepository(db)
        self.redis_client = get_redis_client()

    def get_item(self, item_id: UUID) -> Optional[InventoryItemResponse]:
        """Get inventory item by ID"""
        item = self.repository.get_item(item_id)
        return InventoryItemResponse.model_validate(item) if item else None

    def get_item_by_barcode(self, barcode: str) -> Optional[InventoryItemResponse]:
        """Get inventory item by barcode"""
        item = self.repository.get_item_by_barcode(barcode)
        return InventoryItemResponse.model_validate(item) if item else None

    def get_items(
        self, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        location_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> List[InventoryItemResponse]:
        """Get inventory items with filtering"""
        items = self.repository.get_items(skip, limit, category, location_id, active_only)
        return [InventoryItemResponse.model_validate(item) for item in items]

    def create_item(self, item_data: InventoryItemCreate) -> InventoryItemResponse:
        """Create new inventory item"""
        item = self.repository.create_item(item_data)
        
        # Clear cache for items list
        self._clear_items_cache()
        
        return InventoryItemResponse.model_validate(item)

    def update_item(self, item_id: UUID, item_data: InventoryItemUpdate) -> Optional[InventoryItemResponse]:
        """Update inventory item"""
        item = self.repository.update_item(item_id, item_data)
        if not item:
            return None
        
        # Clear cache
        self._clear_item_cache(item_id)
        self._clear_items_cache()
        
        return InventoryItemResponse.model_validate(item)

    def delete_item(self, item_id: UUID) -> bool:
        """Delete inventory item (soft delete)"""
        success = self.repository.delete_item(item_id)
        if success:
            self._clear_item_cache(item_id)
            self._clear_items_cache()
        return success

    def get_stock_level(self, item_id: UUID, location_id: UUID) -> Optional[StockLevelResponse]:
        """Get stock level for item at location"""
        # Try cache first
        cache_key = f"stock:{location_id}:{item_id}"
        cached_stock = self.redis_client.get(cache_key)
        
        if cached_stock:
            return StockLevelResponse.model_validate_json(cached_stock)
        
        stock = self.repository.get_stock_level(item_id, location_id)
        if stock:
            stock_response = StockLevelResponse.model_validate(stock)
            # Cache for 5 minutes
            self.redis_client.setex(
                cache_key, 
                300, 
                stock_response.model_dump_json()
            )
            return stock_response
        return None

    def get_stock_levels_by_location(self, location_id: UUID) -> List[StockLevelResponse]:
        """Get all stock levels for a location"""
        stocks = self.repository.get_stock_levels_by_location(location_id)
        return [StockLevelResponse.model_validate(stock) for stock in stocks]

    def get_stock_levels_by_item(self, item_id: UUID) -> List[StockLevelResponse]:
        """Get all stock levels for an item"""
        stocks = self.repository.get_stock_levels_by_item(item_id)
        return [StockLevelResponse.model_validate(stock) for stock in stocks]

    def update_stock_level(
        self, 
        item_id: UUID, 
        location_id: UUID, 
        stock_data: StockLevelCreate
    ) -> StockLevelResponse:
        """Create or update stock level"""
        stock = self.repository.create_or_update_stock_level(item_id, location_id, stock_data)
        
        # Clear cache
        self._clear_stock_cache(item_id, location_id)
        
        return StockLevelResponse.model_validate(stock)

    def adjust_stock(
        self, 
        item_id: UUID, 
        location_id: UUID, 
        quantity_change: float,
        user_id: UUID,
        transaction_type: TransactionType = TransactionType.ADJUSTMENT,
        notes: Optional[str] = None
    ) -> Optional[StockLevelResponse]:
        """Adjust stock level with audit trail"""
        stock = self.repository.adjust_stock(
            item_id, location_id, quantity_change, user_id, transaction_type, notes
        )
        
        if stock:
            # Clear cache
            self._clear_stock_cache(item_id, location_id)
            
            # Check for low stock alerts
            self._check_low_stock_alert(item_id, location_id, stock.current_stock)
            
            return StockLevelResponse.model_validate(stock)
        return None

    def get_low_stock_items(self, location_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get items with stock below reorder point"""
        low_stock_items = self.repository.get_low_stock_items(location_id)
        
        result = []
        for item, stock in low_stock_items:
            result.append({
                "item": InventoryItemResponse.model_validate(item),
                "stock": StockLevelResponse.model_validate(stock),
                "shortage": item.reorder_point - stock.current_stock
            })
        
        return result

    def search_items(self, search_term: str, limit: int = 20) -> List[InventoryItemResponse]:
        """Search items by name, barcode, or SKU"""
        items = self.repository.search_items(search_term, limit)
        return [InventoryItemResponse.model_validate(item) for item in items]

    def scan_barcode(self, barcode: str, location_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Process barcode scan and return item info with stock levels"""
        item = self.repository.get_item_by_barcode(barcode)
        if not item:
            return {"error": "Item not found", "barcode": barcode}
        
        item_response = InventoryItemResponse.model_validate(item)
        result = {"item": item_response}
        
        if location_id:
            stock = self.get_stock_level(item.id, location_id)
            result["stock"] = stock
            
            # Check if stock is low
            if stock and stock.current_stock <= item.reorder_point:
                result["alert"] = {
                    "type": "low_stock",
                    "message": f"Stock is low: {stock.current_stock} {item.unit_of_measure.value}",
                    "reorder_point": item.reorder_point
                }
        else:
            # Get stock for all locations
            stocks = self.get_stock_levels_by_item(item.id)
            result["stock_levels"] = stocks
        
        return result

    def _clear_item_cache(self, item_id: UUID):
        """Clear cache for specific item"""
        pattern = f"item:{item_id}*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)

    def _clear_stock_cache(self, item_id: UUID, location_id: UUID):
        """Clear cache for specific stock level"""
        cache_key = f"stock:{location_id}:{item_id}"
        self.redis_client.delete(cache_key)

    def _clear_items_cache(self):
        """Clear cache for items list"""
        pattern = "items:*"
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)

    def _check_low_stock_alert(self, item_id: UUID, location_id: UUID, current_stock: float):
        """Check if stock level triggers an alert"""
        item = self.repository.get_item(item_id)
        if item and current_stock <= item.reorder_point:
            # Store alert in cache for notification service to pick up
            alert_key = f"alert:low_stock:{location_id}:{item_id}"
            alert_data = {
                "type": "low_stock",
                "item_id": str(item_id),
                "location_id": str(location_id),
                "item_name": item.name,
                "current_stock": current_stock,
                "reorder_point": item.reorder_point,
                "timestamp": datetime.utcnow().isoformat()
            }
            # Store alert for 24 hours
            self.redis_client.setex(alert_key, 86400, json.dumps(alert_data))