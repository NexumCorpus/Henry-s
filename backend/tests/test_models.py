import pytest
from sqlalchemy.exc import IntegrityError
from app.models import (
    User, UserRole, Location, LocationType, Supplier, 
    InventoryItem, StockLevel, Transaction, TransactionType,
    ItemCategory, UnitOfMeasure
)
import uuid
from decimal import Decimal


class TestUserModel:
    """Test cases for User model."""
    
    def test_create_user(self, db_session, sample_user_data):
        """Test creating a user with valid data."""
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == sample_user_data["username"]
        assert user.email == sample_user_data["email"]
        assert user.role == UserRole.BARBACK
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_unique_username(self, db_session, sample_user_data):
        """Test that username must be unique."""
        user1 = User(**sample_user_data)
        db_session.add(user1)
        db_session.commit()
        
        # Try to create another user with same username
        sample_user_data["email"] = "different@example.com"
        user2 = User(**sample_user_data)
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_unique_email(self, db_session, sample_user_data):
        """Test that email must be unique."""
        user1 = User(**sample_user_data)
        db_session.add(user1)
        db_session.commit()
        
        # Try to create another user with same email
        sample_user_data["username"] = "different_user"
        user2 = User(**sample_user_data)
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_roles(self, db_session, sample_user_data):
        """Test different user roles."""
        roles = [UserRole.BARBACK, UserRole.BARTENDER, UserRole.MANAGER, UserRole.ADMIN]
        
        for i, role in enumerate(roles):
            sample_user_data["username"] = f"user_{i}"
            sample_user_data["email"] = f"user_{i}@example.com"
            sample_user_data["role"] = role
            
            user = User(**sample_user_data)
            db_session.add(user)
            db_session.commit()
            
            assert user.role == role


class TestLocationModel:
    """Test cases for Location model."""
    
    def test_create_location(self, db_session, sample_location_data):
        """Test creating a location with valid data."""
        location = Location(**sample_location_data)
        db_session.add(location)
        db_session.commit()
        
        assert location.id is not None
        assert location.name == sample_location_data["name"]
        assert location.type == LocationType.BAR
        assert location.is_active is True
        assert location.created_at is not None
    
    def test_location_types(self, db_session, sample_location_data):
        """Test different location types."""
        types = [LocationType.BAR, LocationType.STORAGE, LocationType.KITCHEN, LocationType.ROOFTOP]
        
        for i, location_type in enumerate(types):
            sample_location_data["name"] = f"Location {i}"
            sample_location_data["type"] = location_type
            
            location = Location(**sample_location_data)
            db_session.add(location)
            db_session.commit()
            
            assert location.type == location_type


class TestSupplierModel:
    """Test cases for Supplier model."""
    
    def test_create_supplier(self, db_session, sample_supplier_data):
        """Test creating a supplier with valid data."""
        supplier = Supplier(**sample_supplier_data)
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.id is not None
        assert supplier.name == sample_supplier_data["name"]
        assert supplier.is_active is True
        assert supplier.is_preferred is False
        assert supplier.created_at is not None
    
    def test_supplier_with_api_credentials(self, db_session, sample_supplier_data):
        """Test supplier with API credentials."""
        api_creds = {"api_key": "test_key", "secret": "test_secret"}
        sample_supplier_data["api_credentials"] = api_creds
        
        supplier = Supplier(**sample_supplier_data)
        db_session.add(supplier)
        db_session.commit()
        
        assert supplier.api_credentials == api_creds


class TestInventoryItemModel:
    """Test cases for InventoryItem model."""
    
    def test_create_inventory_item(self, db_session, sample_inventory_item_data):
        """Test creating an inventory item with valid data."""
        item = InventoryItem(**sample_inventory_item_data)
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.name == sample_inventory_item_data["name"]
        assert item.category == ItemCategory.SPIRITS
        assert item.unit_of_measure == UnitOfMeasure.BOTTLE
        assert item.par_level == 10.0
        assert item.reorder_point == 5.0
    
    def test_inventory_item_with_supplier(self, db_session, sample_inventory_item_data, sample_supplier_data):
        """Test creating inventory item with supplier relationship."""
        # Create supplier first
        supplier = Supplier(**sample_supplier_data)
        db_session.add(supplier)
        db_session.commit()
        
        # Create item with supplier
        sample_inventory_item_data["supplier_id"] = supplier.id
        item = InventoryItem(**sample_inventory_item_data)
        db_session.add(item)
        db_session.commit()
        
        assert item.supplier_id == supplier.id
        assert item.supplier.name == supplier.name
    
    def test_inventory_item_unique_barcode(self, db_session, sample_inventory_item_data):
        """Test that barcode must be unique."""
        item1 = InventoryItem(**sample_inventory_item_data)
        db_session.add(item1)
        db_session.commit()
        
        # Try to create another item with same barcode
        sample_inventory_item_data["name"] = "Different Item"
        item2 = InventoryItem(**sample_inventory_item_data)
        db_session.add(item2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_inventory_item_categories(self, db_session, sample_inventory_item_data):
        """Test different item categories."""
        categories = [
            ItemCategory.SPIRITS, ItemCategory.BEER, ItemCategory.WINE,
            ItemCategory.MIXERS, ItemCategory.GARNISHES, ItemCategory.FOOD,
            ItemCategory.SUPPLIES
        ]
        
        for i, category in enumerate(categories):
            sample_inventory_item_data["name"] = f"Item {i}"
            sample_inventory_item_data["barcode"] = f"12345678{i}"
            sample_inventory_item_data["category"] = category
            
            item = InventoryItem(**sample_inventory_item_data)
            db_session.add(item)
            db_session.commit()
            
            assert item.category == category


class TestStockLevelModel:
    """Test cases for StockLevel model."""
    
    def test_create_stock_level(self, db_session, sample_inventory_item_data, sample_location_data):
        """Test creating a stock level record."""
        # Create dependencies
        item = InventoryItem(**sample_inventory_item_data)
        location = Location(**sample_location_data)
        db_session.add(item)
        db_session.add(location)
        db_session.commit()
        
        # Create stock level
        stock_level = StockLevel(
            item_id=item.id,
            location_id=location.id,
            current_stock=25.0,
            reserved_stock=5.0
        )
        db_session.add(stock_level)
        db_session.commit()
        
        assert stock_level.id is not None
        assert stock_level.current_stock == 25.0
        assert stock_level.reserved_stock == 5.0
        assert stock_level.item.name == item.name
        assert stock_level.location.name == location.name
    
    def test_stock_level_unique_item_location(self, db_session, sample_inventory_item_data, sample_location_data):
        """Test that item-location combination must be unique."""
        # Create dependencies
        item = InventoryItem(**sample_inventory_item_data)
        location = Location(**sample_location_data)
        db_session.add(item)
        db_session.add(location)
        db_session.commit()
        
        # Create first stock level
        stock_level1 = StockLevel(
            item_id=item.id,
            location_id=location.id,
            current_stock=25.0
        )
        db_session.add(stock_level1)
        db_session.commit()
        
        # Try to create another stock level for same item-location
        stock_level2 = StockLevel(
            item_id=item.id,
            location_id=location.id,
            current_stock=30.0
        )
        db_session.add(stock_level2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestTransactionModel:
    """Test cases for Transaction model."""
    
    def test_create_transaction(self, db_session, sample_inventory_item_data, 
                               sample_location_data, sample_user_data):
        """Test creating a transaction record."""
        # Create dependencies
        item = InventoryItem(**sample_inventory_item_data)
        location = Location(**sample_location_data)
        user = User(**sample_user_data)
        db_session.add(item)
        db_session.add(location)
        db_session.add(user)
        db_session.commit()
        
        # Create transaction
        transaction = Transaction(
            item_id=item.id,
            location_id=location.id,
            user_id=user.id,
            transaction_type=TransactionType.SALE,
            quantity=-2.0,
            unit_cost=Decimal("25.99"),
            total_cost=Decimal("51.98"),
            notes="Test sale transaction"
        )
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.id is not None
        assert transaction.transaction_type == TransactionType.SALE
        assert transaction.quantity == -2.0
        assert transaction.unit_cost == Decimal("25.99")
        assert transaction.item.name == item.name
        assert transaction.location.name == location.name
        assert transaction.user.username == user.username
    
    def test_transaction_types(self, db_session, sample_inventory_item_data, 
                              sample_location_data, sample_user_data):
        """Test different transaction types."""
        # Create dependencies
        item = InventoryItem(**sample_inventory_item_data)
        location = Location(**sample_location_data)
        user = User(**sample_user_data)
        db_session.add(item)
        db_session.add(location)
        db_session.add(user)
        db_session.commit()
        
        transaction_types = [
            TransactionType.SALE, TransactionType.ADJUSTMENT, TransactionType.RECEIVE,
            TransactionType.WASTE, TransactionType.TRANSFER, TransactionType.COUNT
        ]
        
        for i, trans_type in enumerate(transaction_types):
            transaction = Transaction(
                item_id=item.id,
                location_id=location.id,
                user_id=user.id,
                transaction_type=trans_type,
                quantity=float(i + 1),
                notes=f"Test {trans_type} transaction"
            )
            db_session.add(transaction)
            db_session.commit()
            
            assert transaction.transaction_type == trans_type