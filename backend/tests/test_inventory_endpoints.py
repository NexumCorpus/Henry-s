import pytest
from uuid import uuid4
from app.core.dependencies import get_current_user
from app.models.location import Location, LocationType
from app.models.inventory import InventoryItem, ItemCategory, UnitOfMeasure, StockLevel
from app.schemas.user import UserResponse


def test_inventory_items_endpoint_exists(client):
    """Test that the inventory items endpoint exists and requires authentication"""
    response = client.get("/api/v1/inventory/items")
    # Should return 401 or 422 without authentication
    assert response.status_code in [401, 422]


def test_create_inventory_item_with_auth(client, db_session):
    """Test creating an inventory item with proper authentication"""
    # Mock authenticated user
    def mock_current_user():
        return UserResponse(
            id=uuid4(),
            username="manager",
            email="manager@example.com",
            role="manager",
            is_active=True
        )
    
    client.app.dependency_overrides[get_current_user] = mock_current_user
    
    item_data = {
        "name": "Test Whiskey",
        "category": "spirits",
        "barcode": "987654321",
        "sku": "WHISKEY001",
        "unit_of_measure": "bottle",
        "cost_per_unit": 35.00,
        "par_level": 8.0,
        "reorder_point": 3.0
    }
    
    response = client.post("/api/v1/inventory/items", json=item_data)
    assert response.status_code == 201
    item = response.json()
    assert item["name"] == "Test Whiskey"
    assert item["category"] == "spirits"


def test_get_inventory_items_with_auth(client, db_session):
    """Test getting inventory items with authentication"""
    # Create test data
    location = Location(
        name="Main Bar",
        type=LocationType.BAR,
        description="Main bar area"
    )
    db_session.add(location)
    
    item = InventoryItem(
        name="Test Vodka",
        category=ItemCategory.SPIRITS,
        barcode="123456789",
        sku="VODKA001",
        unit_of_measure=UnitOfMeasure.BOTTLE,
        cost_per_unit=25.00,
        par_level=10.0,
        reorder_point=5.0
    )
    db_session.add(item)
    db_session.commit()
    
    # Mock authenticated user
    def mock_current_user():
        return UserResponse(
            id=uuid4(),
            username="bartender",
            email="bartender@example.com",
            role="bartender",
            is_active=True
        )
    
    client.app.dependency_overrides[get_current_user] = mock_current_user
    
    response = client.get("/api/v1/inventory/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert any(item_data["name"] == "Test Vodka" for item_data in items)


def test_barcode_scan_endpoint(client, db_session):
    """Test barcode scanning endpoint"""
    # Create test item
    item = InventoryItem(
        name="Scan Test Item",
        category=ItemCategory.SPIRITS,
        barcode="SCAN123",
        unit_of_measure=UnitOfMeasure.BOTTLE,
        par_level=5.0,
        reorder_point=2.0
    )
    db_session.add(item)
    db_session.commit()
    
    # Mock authenticated user
    def mock_current_user():
        return UserResponse(
            id=uuid4(),
            username="barback",
            email="barback@example.com",
            role="barback",
            is_active=True
        )
    
    client.app.dependency_overrides[get_current_user] = mock_current_user
    
    response = client.post("/api/v1/inventory/scan?barcode=SCAN123")
    assert response.status_code == 200
    result = response.json()
    assert "item" in result
    assert result["item"]["name"] == "Scan Test Item"


def test_stock_adjustment_endpoint(client, db_session):
    """Test stock adjustment endpoint"""
    # Create test data
    location = Location(
        name="Test Location",
        type=LocationType.BAR
    )
    db_session.add(location)
    
    item = InventoryItem(
        name="Adjustment Test Item",
        category=ItemCategory.SPIRITS,
        unit_of_measure=UnitOfMeasure.BOTTLE,
        par_level=10.0,
        reorder_point=5.0
    )
    db_session.add(item)
    db_session.commit()
    
    stock = StockLevel(
        item_id=item.id,
        location_id=location.id,
        current_stock=10.0
    )
    db_session.add(stock)
    db_session.commit()
    
    # Mock authenticated user
    def mock_current_user():
        return UserResponse(
            id=uuid4(),
            username="bartender",
            email="bartender@example.com",
            role="bartender",
            is_active=True
        )
    
    client.app.dependency_overrides[get_current_user] = mock_current_user
    
    # Test positive adjustment
    response = client.post(
        f"/api/v1/inventory/adjust/{item.id}/{location.id}?quantity_change=5.0&notes=Received shipment"
    )
    assert response.status_code == 200
    result = response.json()
    assert result["current_stock"] == 15.0


def test_low_stock_alerts_endpoint(client, db_session):
    """Test low stock alerts endpoint"""
    # Create test data with low stock
    location = Location(
        name="Alert Test Location",
        type=LocationType.BAR
    )
    db_session.add(location)
    
    item = InventoryItem(
        name="Low Stock Item",
        category=ItemCategory.SPIRITS,
        unit_of_measure=UnitOfMeasure.BOTTLE,
        par_level=10.0,
        reorder_point=5.0
    )
    db_session.add(item)
    db_session.commit()
    
    # Create stock level below reorder point
    stock = StockLevel(
        item_id=item.id,
        location_id=location.id,
        current_stock=3.0  # Below reorder point of 5.0
    )
    db_session.add(stock)
    db_session.commit()
    
    # Mock authenticated user
    def mock_current_user():
        return UserResponse(
            id=uuid4(),
            username="manager",
            email="manager@example.com",
            role="manager",
            is_active=True
        )
    
    client.app.dependency_overrides[get_current_user] = mock_current_user
    
    response = client.get("/api/v1/inventory/alerts/low-stock")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 1
    assert any(alert["item"]["name"] == "Low Stock Item" for alert in alerts)


def test_permission_restrictions(client, db_session):
    """Test that permission restrictions work correctly"""
    # Mock barback user (limited permissions)
    def mock_barback_user():
        return UserResponse(
            id=uuid4(),
            username="barback",
            email="barback@example.com",
            role="barback",
            is_active=True
        )
    
    client.app.dependency_overrides[get_current_user] = mock_barback_user
    
    # Barback should not be able to create items
    item_data = {
        "name": "Unauthorized Item",
        "category": "spirits",
        "unit_of_measure": "bottle"
    }
    response = client.post("/api/v1/inventory/items", json=item_data)
    assert response.status_code == 403
    
    # But should be able to view items
    response = client.get("/api/v1/inventory/items")
    assert response.status_code == 200