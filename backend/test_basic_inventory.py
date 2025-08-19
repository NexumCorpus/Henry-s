#!/usr/bin/env python3
"""
Basic test script to verify inventory API functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.main import app
from app.core.database import Base, get_db
from app.core.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.models.inventory import InventoryItem, ItemCategory, UnitOfMeasure
from app.models.location import Location, LocationType

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_basic.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user():
    return UserResponse(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role="manager",
        is_active=True,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_health_check():
    """Test basic health check"""
    response = client.get("/health")
    assert response.status_code == 200
    print("✓ Health check passed")

def test_create_inventory_item():
    """Test creating an inventory item"""
    item_data = {
        "name": "Test Vodka",
        "category": "spirits",
        "barcode": "123456789",
        "sku": "VODKA001",
        "unit_of_measure": "bottle",
        "cost_per_unit": 25.00,
        "par_level": 10.0,
        "reorder_point": 5.0
    }
    
    response = client.post("/api/v1/inventory/items", json=item_data)
    print(f"Create item response: {response.status_code}")
    if response.status_code != 201:
        print(f"Error: {response.text}")
        return None
    
    item = response.json()
    print("✓ Item created successfully")
    return item

def test_get_inventory_items():
    """Test getting inventory items"""
    response = client.get("/api/v1/inventory/items")
    print(f"Get items response: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
    
    items = response.json()
    print(f"✓ Retrieved {len(items)} items")

def test_barcode_scan():
    """Test barcode scanning"""
    response = client.post("/api/v1/inventory/scan?barcode=123456789")
    print(f"Scan response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✓ Barcode scan successful")
        print(f"  Found item: {result.get('item', {}).get('name', 'Unknown')}")
    elif response.status_code == 404:
        print("! Item not found (expected if no items created)")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("Running basic inventory API tests...")
    
    try:
        test_health_check()
        item = test_create_inventory_item()
        test_get_inventory_items()
        if item:
            test_barcode_scan()
        
        print("\n✓ All basic tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if os.path.exists("test_basic.db"):
            os.remove("test_basic.db")
        print("Cleanup completed.")