from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from app.models.inventory import InventoryItem, StockLevel
from app.models.transaction import Transaction, TransactionType
from app.schemas.inventory import InventoryItemCreate, InventoryItemUpdate, StockLevelCreate, StockLevelUpdate
from app.schemas.transaction import TransactionCreate


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_item(self, item_id: UUID) -> Optional[InventoryItem]:
        """Get a single inventory item by ID"""
        return self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()

    def get_item_by_barcode(self, barcode: str) -> Optional[InventoryItem]:
        """Get inventory item by barcode"""
        return self.db.query(InventoryItem).filter(InventoryItem.barcode == barcode).first()

    def get_items(
        self, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        location_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> List[InventoryItem]:
        """Get inventory items with optional filtering"""
        query = self.db.query(InventoryItem).options(joinedload(InventoryItem.stock_levels))
        
        if active_only:
            query = query.filter(InventoryItem.is_active == "true")
        
        if category:
            query = query.filter(InventoryItem.category == category)
        
        if location_id:
            query = query.join(StockLevel).filter(StockLevel.location_id == location_id)
        
        return query.offset(skip).limit(limit).all()

    def create_item(self, item_data: InventoryItemCreate) -> InventoryItem:
        """Create a new inventory item"""
        db_item = InventoryItem(**item_data.model_dump())
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def update_item(self, item_id: UUID, item_data: InventoryItemUpdate) -> Optional[InventoryItem]:
        """Update an existing inventory item"""
        db_item = self.get_item(item_id)
        if not db_item:
            return None
        
        update_data = item_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def delete_item(self, item_id: UUID) -> bool:
        """Soft delete an inventory item"""
        db_item = self.get_item(item_id)
        if not db_item:
            return False
        
        db_item.is_active = "false"
        self.db.commit()
        return True

    def get_stock_level(self, item_id: UUID, location_id: UUID) -> Optional[StockLevel]:
        """Get stock level for specific item and location"""
        return self.db.query(StockLevel).filter(
            and_(StockLevel.item_id == item_id, StockLevel.location_id == location_id)
        ).first()

    def get_stock_levels_by_location(self, location_id: UUID) -> List[StockLevel]:
        """Get all stock levels for a location"""
        return self.db.query(StockLevel).options(joinedload(StockLevel.item)).filter(
            StockLevel.location_id == location_id
        ).all()

    def get_stock_levels_by_item(self, item_id: UUID) -> List[StockLevel]:
        """Get all stock levels for an item across locations"""
        return self.db.query(StockLevel).options(joinedload(StockLevel.location)).filter(
            StockLevel.item_id == item_id
        ).all()

    def create_or_update_stock_level(
        self, 
        item_id: UUID, 
        location_id: UUID, 
        stock_data: StockLevelCreate
    ) -> StockLevel:
        """Create or update stock level for item at location"""
        existing_stock = self.get_stock_level(item_id, location_id)
        
        if existing_stock:
            # Update existing stock level
            update_data = stock_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field not in ['item_id', 'location_id']:  # Don't update IDs
                    setattr(existing_stock, field, value)
            self.db.commit()
            self.db.refresh(existing_stock)
            return existing_stock
        else:
            # Create new stock level
            db_stock = StockLevel(
                item_id=item_id,
                location_id=location_id,
                **stock_data.model_dump(exclude={'item_id', 'location_id'})
            )
            self.db.add(db_stock)
            self.db.commit()
            self.db.refresh(db_stock)
            return db_stock

    def adjust_stock(
        self, 
        item_id: UUID, 
        location_id: UUID, 
        quantity_change: float,
        user_id: UUID,
        transaction_type: TransactionType = TransactionType.ADJUSTMENT,
        notes: Optional[str] = None
    ) -> Optional[StockLevel]:
        """Adjust stock level and create transaction record"""
        stock_level = self.get_stock_level(item_id, location_id)
        if not stock_level:
            return None
        
        # Update stock level
        stock_level.current_stock += quantity_change
        if stock_level.current_stock < 0:
            stock_level.current_stock = 0
        
        # Create transaction record
        transaction = Transaction(
            item_id=item_id,
            location_id=location_id,
            user_id=user_id,
            transaction_type=transaction_type,
            quantity=quantity_change,
            notes=notes
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(stock_level)
        return stock_level

    def get_low_stock_items(self, location_id: Optional[UUID] = None) -> List[tuple]:
        """Get items with stock below reorder point"""
        query = self.db.query(InventoryItem, StockLevel).join(StockLevel).filter(
            and_(
                InventoryItem.is_active == "true",
                StockLevel.current_stock <= InventoryItem.reorder_point
            )
        )
        
        if location_id:
            query = query.filter(StockLevel.location_id == location_id)
        
        return query.all()

    def search_items(self, search_term: str, limit: int = 20) -> List[InventoryItem]:
        """Search items by name, barcode, or SKU"""
        search_pattern = f"%{search_term}%"
        return self.db.query(InventoryItem).filter(
            and_(
                InventoryItem.is_active == "true",
                or_(
                    InventoryItem.name.ilike(search_pattern),
                    InventoryItem.barcode.ilike(search_pattern),
                    InventoryItem.sku.ilike(search_pattern)
                )
            )
        ).limit(limit).all()