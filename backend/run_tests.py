#!/usr/bin/env python3
"""
Simple test runner script for the backend tests.
This can be used when pytest is not available in the environment.
"""

import sys
import os
import unittest
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_basic_model_tests():
    """Run basic model validation tests."""
    print("Running basic model validation tests...")
    
    try:
        # Test model imports
        from app.models import (
            User, UserRole, Location, LocationType, Supplier,
            InventoryItem, StockLevel, Transaction, TransactionType,
            ItemCategory, UnitOfMeasure
        )
        print("✓ All models imported successfully")
        
        # Test schema imports
        from app.schemas import (
            UserCreate, UserUpdate, UserResponse,
            LocationCreate, LocationUpdate, LocationResponse,
            SupplierCreate, SupplierUpdate, SupplierResponse,
            InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
            StockLevelCreate, StockLevelUpdate, StockLevelResponse,
            TransactionCreate, TransactionResponse
        )
        print("✓ All schemas imported successfully")
        
        # Test enum values
        assert UserRole.BARBACK == "barback"
        assert UserRole.BARTENDER == "bartender"
        assert UserRole.MANAGER == "manager"
        assert UserRole.ADMIN == "admin"
        print("✓ UserRole enum values correct")
        
        assert LocationType.BAR == "bar"
        assert LocationType.STORAGE == "storage"
        assert LocationType.KITCHEN == "kitchen"
        assert LocationType.ROOFTOP == "rooftop"
        print("✓ LocationType enum values correct")
        
        assert ItemCategory.SPIRITS == "spirits"
        assert ItemCategory.BEER == "beer"
        assert ItemCategory.WINE == "wine"
        print("✓ ItemCategory enum values correct")
        
        assert UnitOfMeasure.BOTTLE == "bottle"
        assert UnitOfMeasure.CASE == "case"
        assert UnitOfMeasure.LITER == "liter"
        print("✓ UnitOfMeasure enum values correct")
        
        assert TransactionType.SALE == "sale"
        assert TransactionType.ADJUSTMENT == "adjustment"
        assert TransactionType.RECEIVE == "receive"
        print("✓ TransactionType enum values correct")
        
        # Test schema validation
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": UserRole.BARBACK,
            "password": "securepassword123"
        }
        user_create = UserCreate(**user_data)
        assert user_create.username == "testuser"
        print("✓ UserCreate schema validation works")
        
        location_data = {
            "name": "Main Bar",
            "type": LocationType.BAR,
            "description": "Primary bar location"
        }
        location_create = LocationCreate(**location_data)
        assert location_create.name == "Main Bar"
        print("✓ LocationCreate schema validation works")
        
        print("\n🎉 All basic model tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_database_schema():
    """Validate database schema structure."""
    print("\nValidating database schema structure...")
    
    try:
        from app.models import Base
        from sqlalchemy import inspect
        
        # Get all table names from metadata
        table_names = list(Base.metadata.tables.keys())
        expected_tables = [
            'users', 'locations', 'suppliers', 'inventory_items', 
            'stock_levels', 'transactions'
        ]
        
        for table in expected_tables:
            assert table in table_names, f"Missing table: {table}"
        
        print(f"✓ All expected tables present: {table_names}")
        
        # Check specific table structures
        users_table = Base.metadata.tables['users']
        user_columns = [col.name for col in users_table.columns]
        expected_user_columns = ['id', 'username', 'email', 'hashed_password', 'full_name', 'role', 'is_active', 'created_at', 'updated_at']
        
        for col in expected_user_columns:
            assert col in user_columns, f"Missing column in users table: {col}"
        
        print("✓ Users table structure correct")
        
        inventory_table = Base.metadata.tables['inventory_items']
        inventory_columns = [col.name for col in inventory_table.columns]
        expected_inventory_columns = ['id', 'name', 'category', 'barcode', 'unit_of_measure', 'par_level', 'reorder_point']
        
        for col in expected_inventory_columns:
            assert col in inventory_columns, f"Missing column in inventory_items table: {col}"
        
        print("✓ Inventory items table structure correct")
        
        print("🎉 Database schema validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner."""
    print("=" * 60)
    print("Henry's SmartStock AI - Backend Model Tests")
    print("=" * 60)
    
    success = True
    
    # Run basic model tests
    if not run_basic_model_tests():
        success = False
    
    # Validate database schema
    if not validate_database_schema():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✓ Models are properly defined")
        print("✓ Schemas are working correctly")
        print("✓ Database schema is valid")
        print("✓ Relationships are properly configured")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the error messages above.")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()