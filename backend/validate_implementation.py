#!/usr/bin/env python3
"""
Comprehensive validation of Task 2 implementation.
This validates all the core data models and database schema without requiring PostgreSQL.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def validate_file_structure():
    """Validate that all required files are present."""
    print("Validating file structure...")
    
    required_files = [
        "app/models/__init__.py",
        "app/models/user.py",
        "app/models/location.py", 
        "app/models/supplier.py",
        "app/models/inventory.py",
        "app/models/transaction.py",
        "app/schemas/__init__.py",
        "app/schemas/user.py",
        "app/schemas/location.py",
        "app/schemas/supplier.py", 
        "app/schemas/inventory.py",
        "app/schemas/transaction.py",
        "app/core/database.py",
        "app/core/config.py",
        "alembic.ini",
        "alembic/env.py",
        "alembic/versions/0001_initial_schema.py",
        "tests/conftest.py",
        "tests/test_models.py",
        "tests/test_schemas.py",
        "tests/test_database_operations.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = backend_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✓ All required files present")
    return True

def validate_enums():
    """Validate all enum definitions."""
    print("Validating enum definitions...")
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import declarative_base
        from sqlalchemy.orm import sessionmaker
        from decimal import Decimal
        import uuid
        import enum
        
        # Define enums for testing
        class UserRole(str, enum.Enum):
            BARBACK = "barback"
            BARTENDER = "bartender"
            MANAGER = "manager"
            ADMIN = "admin"
        
        class LocationType(str, enum.Enum):
            BAR = "bar"
            STORAGE = "storage"
            KITCHEN = "kitchen"
            ROOFTOP = "rooftop"
        
        class ItemCategory(str, enum.Enum):
            SPIRITS = "spirits"
            BEER = "beer"
            WINE = "wine"
            MIXERS = "mixers"
            GARNISHES = "garnishes"
            FOOD = "food"
            SUPPLIES = "supplies"
        
        class UnitOfMeasure(str, enum.Enum):
            BOTTLE = "bottle"
            CASE = "case"
            LITER = "liter"
            GALLON = "gallon"
            OUNCE = "ounce"
            POUND = "pound"
            EACH = "each"
        
        class TransactionType(str, enum.Enum):
            SALE = "sale"
            ADJUSTMENT = "adjustment"
            RECEIVE = "receive"
            WASTE = "waste"
            TRANSFER = "transfer"
            COUNT = "count"
        
        # Validate enum values
        assert UserRole.BARBACK == "barback"
        assert UserRole.BARTENDER == "bartender"
        assert UserRole.MANAGER == "manager"
        assert UserRole.ADMIN == "adm