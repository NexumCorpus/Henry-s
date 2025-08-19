import pytest
from pydantic import ValidationError
from decimal import Decimal
from uuid import uuid4
from app.schemas import (
    UserCreate, UserUpdate, UserResponse,
    LocationCreate, LocationUpdate, LocationResponse,
    SupplierCreate, SupplierUpdate, SupplierResponse,
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    StockLevelCreate, StockLevelUpdate, StockLevelResponse,
    TransactionCreate, TransactionResponse
)
from app.models import UserRole, LocationType, ItemCategory, UnitOfMeasure, TransactionType


class TestUserSchemas:
    """Test cases for User schemas."""
    
    def test_user_create_valid(self):
        """Test creating a user with valid data."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": UserRole.BARBACK,
            "password": "securepassword123"
        }
        user = UserCreate(**user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.BARBACK
        assert user.password == "securepassword123"
    
    def test_user_create_invalid_email(self):
        """Test user creation with invalid email."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "full_name": "Test User",
            "password": "securepassword123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_create_short_password(self):
        """Test user creation with short password."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "short"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_update_partial(self):
        """Test partial user update."""
        update_data = {
            "full_name": "Updated Name",
            "role": UserRole.MANAGER
        }
        user_update = UserUpdate(**update_data)
        
        assert user_update.full_name == "Updated Name"
        assert user_update.role == UserRole.MANAGER
        assert user_update.username is None
        assert user_update.email is None


class TestLocationSchemas:
    """Test cases for Location schemas."""
    
    def test_location_create_valid(self):
        """Test creating a location with valid data."""
        location_data = {
            "name": "Main Bar",
            "type": LocationType.BAR,
            "description": "Primary bar location"
        }
        location = LocationCreate(**location_data)
        
        assert location.name == "Main Bar"
        assert location.type == LocationType.BAR
        assert location.description == "Primary bar location"
        assert location.is_active is True
    
    def test_location_create_empty_name(self):
        """Test location creation with empty name."""
        location_data = {
            "name": "",
            "type": LocationType.BAR
        }
        
        with pytest.raises(ValidationError):
            LocationCreate(**location_data)
    
    def test_location_update_partial(self):
        """Test partial location update."""
        update_data = {
            "description": "Updated description",
            "is_active": False
        }
        location_update = LocationUpdate(**update_data)
        
        assert location_update.description == "Updated description"
        assert location_update.is_active is False
        assert location_update.name is None


class TestSupplierSchemas:
    """Test cases for Supplier schemas."""
    
    def test_supplier_create_valid(self):
        """Test creating a supplier with valid data."""
        supplier_data = {
            "name": "Test Supplier",
            "contact_name": "John Doe",
            "email": "supplier@example.com",
            "phone": "555-1234",
            "api_credentials": {"api_key": "test_key"}
        }
        supplier = SupplierCreate(**supplier_data)
        
        assert supplier.name == "Test Supplier"
        assert supplier.contact_name == "John Doe"
        assert supplier.email == "supplier@example.com"
        assert supplier.api_credentials == {"api_key": "test_key"}
    
    def test_supplier_create_invalid_email(self):
        """Test supplier creation with invalid email."""
        supplier_data = {
            "name": "Test Supplier",
            "email": "invalid-email"
        }
        
        with pytest.raises(ValidationError):
            SupplierCreate(**supplier_data)
    
    def test_supplier_response_excludes_credentials(self):
        """Test that supplier response excludes API credentials."""
        supplier_data = {
            "id": uuid4(),
            "name": "Test Supplier",
            "contact_name": "John Doe",
            "email": "supplier@example.com",
            "phone": "555-1234",
            "address": "123 Test St",
            "is_active": True,
            "is_preferred": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        # This should work without api_credentials
        supplier_response = SupplierResponse(**supplier_data)
        assert supplier_response.name == "Test Supplier"


class TestInventoryItemSchemas:
    """Test cases for InventoryItem schemas."""
    
    def test_inventory_item_create_valid(self):
        """Test creating an inventory item with valid data."""
        item_data = {
            "name": "Test Vodka",
            "category": ItemCategory.SPIRITS,
            "barcode": "123456789",
            "unit_of_measure": UnitOfMeasure.BOTTLE,
            "cost_per_unit": Decimal("25.99"),
            "selling_price": Decimal("45.00"),
            "par_level": 10.0,
            "reorder_point": 5.0
        }
        item = InventoryItemCreate(**item_data)
        
        assert item.name == "Test Vodka"
        assert item.category == ItemCategory.SPIRITS
        assert item.cost_per_unit == Decimal("25.99")
        assert item.par_level == 10.0
    
    def test_inventory_item_negative_cost(self):
        """Test inventory item with negative cost."""
        item_data = {
            "name": "Test Item",
            "category": ItemCategory.SPIRITS,
            "unit_of_measure": UnitOfMeasure.BOTTLE,
            "cost_per_unit": Decimal("-10.00")
        }
        
        with pytest.raises(ValidationError):
            InventoryItemCreate(**item_data)
    
    def test_inventory_item_negative_par_level(self):
        """Test inventory item with negative par level."""
        item_data = {
            "name": "Test Item",
            "category": ItemCategory.SPIRITS,
            "unit_of_measure": UnitOfMeasure.BOTTLE,
            "par_level": -5.0
        }
        
        with pytest.raises(ValidationError):
            InventoryItemCreate(**item_data)


class TestStockLevelSchemas:
    """Test cases for StockLevel schemas."""
    
    def test_stock_level_create_valid(self):
        """Test creating a stock level with valid data."""
        stock_data = {
            "item_id": uuid4(),
            "location_id": uuid4(),
            "current_stock": 25.0,
            "reserved_stock": 5.0
        }
        stock_level = StockLevelCreate(**stock_data)
        
        assert stock_level.current_stock == 25.0
        assert stock_level.reserved_stock == 5.0
    
    def test_stock_level_negative_stock(self):
        """Test stock level with negative stock."""
        stock_data = {
            "item_id": uuid4(),
            "location_id": uuid4(),
            "current_stock": -10.0
        }
        
        with pytest.raises(ValidationError):
            StockLevelCreate(**stock_data)


class TestTransactionSchemas:
    """Test cases for Transaction schemas."""
    
    def test_transaction_create_valid(self):
        """Test creating a transaction with valid data."""
        transaction_data = {
            "item_id": uuid4(),
            "location_id": uuid4(),
            "transaction_type": TransactionType.SALE,
            "quantity": -2.0,
            "unit_cost": Decimal("25.99"),
            "total_cost": Decimal("51.98"),
            "notes": "Test transaction"
        }
        transaction = TransactionCreate(**transaction_data)
        
        assert transaction.transaction_type == TransactionType.SALE
        assert transaction.quantity == -2.0
        assert transaction.unit_cost == Decimal("25.99")
    
    def test_transaction_zero_quantity(self):
        """Test transaction with zero quantity."""
        transaction_data = {
            "item_id": uuid4(),
            "location_id": uuid4(),
            "transaction_type": TransactionType.SALE,
            "quantity": 0.0
        }
        
        with pytest.raises(ValidationError):
            TransactionCreate(**transaction_data)
    
    def test_transaction_negative_cost(self):
        """Test transaction with negative cost."""
        transaction_data = {
            "item_id": uuid4(),
            "location_id": uuid4(),
            "transaction_type": TransactionType.SALE,
            "quantity": 1.0,
            "unit_cost": Decimal("-10.00")
        }
        
        with pytest.raises(ValidationError):
            TransactionCreate(**transaction_data)