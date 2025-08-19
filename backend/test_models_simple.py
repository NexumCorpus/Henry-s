#!/usr/bin/env python3
"""
Simplified model tests that work without pydantic.
Tests the core SQLAlchemy models and database functionality.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_model_imports():
    """Test that all models can be imported successfully."""
    print("Testing model imports...")
    
    try:
        from app.models.user import User, UserRole
        from app.models.location import Location, LocationType
        from app.models.supplier import Supplier
        from app.models.inventory import InventoryItem, StockLevel, ItemCategory, UnitOfMeasure
        from app.models.transaction import Transaction, TransactionType
        
        print("✓ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enum_values():
    """Test that all enum values are correct."""
    print("Testing enum values...")
    
    try:
        from app.models.user import UserRole
        from app.models.location import LocationType
        from app.models.inventory import ItemCategory, UnitOfMeasure
        from app.models.transaction import TransactionType
        
        # Test UserRole enum
        assert UserRole.BARBACK == "barback"
        assert UserRole.BARTENDER == "bartender"
        assert UserRole.MANAGER == "manager"
        assert UserRole.ADMIN == "admin"
        print("✓ UserRole enum values correct")
        
        # Test LocationType enum
        assert LocationType.BAR == "bar"
        assert LocationType.STORAGE == "storage"
        assert LocationType.KITCHEN == "kitchen"
        assert LocationType.ROOFTOP == "rooftop"
        print("✓ LocationType enum values correct")
        
        # Test ItemCategory enum
        assert ItemCategory.SPIRITS == "spirits"
        assert ItemCategory.BEER == "beer"
        assert ItemCategory.WINE == "wine"
        assert ItemCategory.MIXERS == "mixers"
        assert ItemCategory.GARNISHES == "garnishes"
        assert ItemCategory.FOOD == "food"
        assert ItemCategory.SUPPLIES == "supplies"
        print("✓ ItemCategory enum values correct")
        
        # Test UnitOfMeasure enum
        assert UnitOfMeasure.BOTTLE == "bottle"
        assert UnitOfMeasure.CASE == "case"
        assert UnitOfMeasure.LITER == "liter"
        assert UnitOfMeasure.GALLON == "gallon"
        assert UnitOfMeasure.OUNCE == "ounce"
        assert UnitOfMeasure.POUND == "pound"
        assert UnitOfMeasure.EACH == "each"
        print("✓ UnitOfMeasure enum values correct")
        
        # Test TransactionType enum
        assert TransactionType.SALE == "sale"
        assert TransactionType.ADJUSTMENT == "adjustment"
        assert TransactionType.RECEIVE == "receive"
        assert TransactionType.WASTE == "waste"
        assert TransactionType.TRANSFER == "transfer"
        assert TransactionType.COUNT == "count"
        print("✓ TransactionType enum values correct")
        
        return True
    except Exception as e:
        print(f"❌ Enum test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_creation():
    """Test creating model instances."""
    print("Testing model instance creation...")
    
    try:
        from app.models.user import User, UserRole
        from app.models.location import Location, LocationType
        from app.models.supplier import Supplier
        from app.models.inventory import InventoryItem, ItemCategory, UnitOfMeasure
        from decimal import Decimal
        import uuid
        
        # Test User creation
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.BARBACK,
            hashed_password="hashed_password"
        )
        assert user.username == "testuser"
        assert user.role == UserRole.BARBACK
        print("✓ User model creation works")
        
        # Test Location creation
        location = Location(
            name="Main Bar",
            type=LocationType.BAR,
            description="Primary bar location"
        )
        assert location.name == "Main Bar"
        assert location.type == LocationType.BAR
        print("✓ Location model creation works")
        
        # Test Supplier creation
        supplier = Supplier(
            name="Test Supplier",
            contact_name="John Doe",
            email="supplier@example.com",
            is_active=True,
            is_preferred=False
        )
        assert supplier.name == "Test Supplier"
        assert supplier.is_active is True
        print("✓ Supplier model creation works")
        
        # Test InventoryItem creation
        item = InventoryItem(
            name="Test Vodka",
            category=ItemCategory.SPIRITS,
            barcode="123456789",
            unit_of_measure=UnitOfMeasure.BOTTLE,
            cost_per_unit=Decimal("25.99"),
            par_level=10.0,
            reorder_point=5.0,
            is_active="true"
        )
        assert item.name == "Test Vodka"
        assert item.category == ItemCategory.SPIRITS
        assert item.cost_per_unit == Decimal("25.99")
        print("✓ InventoryItem model creation works")
        
        return True
    except Exception as e:
        print(f"❌ Model creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_schema():
    """Test database schema structure."""
    print("Testing database schema...")
    
    try:
        from app.models import Base
        
        # Get all table names from metadata
        table_names = list(Base.metadata.tables.keys())
        expected_tables = [
            'users', 'locations', 'suppliers', 'inventory_items', 
            'stock_levels', 'transactions'
        ]
        
        for table in expected_tables:
            assert table in table_names, f"Missing table: {table}"
        
        print(f"✓ All expected tables present: {table_names}")
        
        # Check users table structure
        users_table = Base.metadata.tables['users']
        user_columns = [col.name for col in users_table.columns]
        expected_user_columns = [
            'id', 'username', 'email', 'hashed_password', 'full_name', 
            'role', 'is_active', 'created_at', 'updated_at'
        ]
        
        for col in expected_user_columns:
            assert col in user_columns, f"Missing column in users table: {col}"
        
        print("✓ Users table structure correct")
        
        # Check inventory_items table structure
        inventory_table = Base.metadata.tables['inventory_items']
        inventory_columns = [col.name for col in inventory_table.columns]
        expected_inventory_columns = [
            'id', 'name', 'category', 'barcode', 'unit_of_measure', 
            'par_level', 'reorder_point', 'supplier_id'
        ]
        
        for col in expected_inventory_columns:
            assert col in inventory_columns, f"Missing column in inventory_items table: {col}"
        
        print("✓ Inventory items table structure correct")
        
        # Check relationships
        from app.models.inventory import InventoryItem
        from app.models.supplier import Supplier
        
        # Check if relationship attributes exist
        assert hasattr(InventoryItem, 'supplier'), "InventoryItem missing supplier relationship"
        assert hasattr(Supplier, 'inventory_items'), "Supplier missing inventory_items relationship"
        
        print("✓ Model relationships configured correctly")
        
        return True
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_in_memory_database():
    """Test with in-memory SQLite database."""
    print("Testing with in-memory database...")
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models import Base
        from app.models.user import User, UserRole
        from app.models.location import Location, LocationType
        from app.models.inventory import InventoryItem, ItemCategory, UnitOfMeasure
        from decimal import Decimal
        
        # Create in-memory SQLite database
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # Test creating and saving a user
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=UserRole.BARTENDER,
            hashed_password="hashed_password"
        )
        session.add(user)
        session.commit()
        
        # Test querying the user
        retrieved_user = session.query(User).filter(User.username == "testuser").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.role == UserRole.BARTENDER
        
        print("✓ User CRUD operations work")
        
        # Test creating a location
        location = Location(
            name="Main Bar",
            type=LocationType.BAR,
            description="Primary bar location"
        )
        session.add(location)
        session.commit()
        
        # Test creating an inventory item
        item = InventoryItem(
            name="Premium Vodka",
            category=ItemCategory.SPIRITS,
            barcode="123456789012",
            unit_of_measure=UnitOfMeasure.BOTTLE,
            cost_per_unit=Decimal("28.99"),
            par_level=6.0,
            reorder_point=3.0,
            is_active="true"
        )
        session.add(item)
        session.commit()
        
        # Test querying items by category
        spirits = session.query(InventoryItem).filter(
            InventoryItem.category == ItemCategory.SPIRITS
        ).all()
        assert len(spirits) == 1
        assert spirits[0].name == "Premium Vodka"
        
        print("✓ Complex database operations work")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner."""
    print("=" * 60)
    print("Henry's SmartStock AI - Simplified Model Tests")
    print("=" * 60)
    
    success = True
    
    # Run all tests
    tests = [
        test_model_imports,
        test_enum_values,
        test_model_creation,
        test_database_schema,
        test_in_memory_database
    ]
    
    for test in tests:
        if not test():
            success = False
        print()  # Add spacing between tests
    
    print("=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✓ Models are properly defined")
        print("✓ Enums are working correctly")
        print("✓ Database schema is valid")
        print("✓ Relationships are properly configured")
        print("✓ Database operations work correctly")
        print("\nTask 2 implementation is COMPLETE and VALIDATED!")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the error messages above.")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()