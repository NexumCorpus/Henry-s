"""
Integration tests for inventory management API endpoints.
Tests the complete functionality of task 4: Build basic inventory management API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal

from app.main import app
from app.core.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.location import Location, LocationType
from app.models.supplier import Supplier
from app.models.inventory import InventoryItem, ItemCategory, UnitOfMeasure, StockLevel
from app.models.transaction import Transaction, TransactionType
from app.schemas.user import UserResponse


# Test client
client = TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Mock admin user for testing"""
    return UserResponse(
        id=uuid4(),
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        role="admin",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_manager_user():
    """Mock manager user for testing"""
    return UserResponse(
        id=uuid4(),
        username="manager",
        email="manager@example.com",
        full_name="Manager User",
        role="manager",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_bartender_user():
    """Mock bartender user for testing"""
    return UserResponse(
        id=uuid4(),
        username="bartender",
        email="bartender@example.com",
        full_name="Bartender User",
        role="bartender",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_barback_user():
    """Mock barback user for testing"""
    return UserResponse(
        id=uuid4(),
        username="barback",
        email="barback@example.com",
        full_name="Barback User",
        role="barback",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def test_location(db_session):
    """Create a test location"""
    location = Location(
        name="Main Bar",
        type=LocationType.BAR,
        description="Main bar area",
        is_active=True
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location


@pytest.fixture
def test_supplier(db_session):
    """Create a test supplier"""
    supplier = Supplier(
        name="Test Supplier",
        contact_name="John Doe",
        email="supplier@example.com",
        phone="555-0123",
        is_active=True,
        is_preferred=True
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


@pytest.fixture
def test_item(db_session, test_supplier):
    """Create a test inventory item"""
    item = InventoryItem(
        name="Test Vodka",
        category=ItemCategory.SPIRITS,
        barcode="123456789",
        sku="VODKA001",
        description="Premium vodka for testing",
        unit_of_measure=UnitOfMeasure.BOTTLE,
        cost_per_unit=Decimal("25.00"),
        selling_price=Decimal("45.00"),
        par_level=10.0,
        reorder_point=5.0,
        supplier_id=test_supplier.id,
        expiration_days=365.0,
        is_active="true"
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def test_stock_level(db_session, test_item, test_location):
    """Create a test stock level"""
    stock = StockLevel(
        item_id=test_item.id,
        location_id=test_location.id,
        current_stock=8.0,
        reserved_stock=1.0,
        last_counted=datetime.now(timezone.utc)
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    return stock


class TestInventoryItemCRUD:
    """Test inventory item CRUD operations"""

    def test_get_inventory_items(self, db_session, test_item, mock_manager_user):
        """Test getting inventory items list"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        response = client.get("/api/v1/inventory/items")
        assert response.status_code == 200
        
        items = response.json()
        assert len(items) >= 1
        assert any(item["name"] == "Test Vodka" for item in items)
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_inventory_item_by_id(self, db_session, test_item, mock_manager_user):
        """Test getting specific inventory item"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        response = client.get(f"/api/v1/inventory/items/{test_item.id}")
        assert response.status_code == 200
        
        item = response.json()
        assert item["name"] == "Test Vodka"
        assert item["category"] == "spirits"
        assert item["barcode"] == "123456789"
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_inventory_item_not_found(self, mock_manager_user):
        """Test getting non-existent inventory item"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/inventory/items/{fake_id}")
        assert response.status_code == 404
        
        # Clean up
        app.dependency_overrides.clear()

    def test_create_inventory_item(self, mock_manager_user):
        """Test creating new inventory item"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        # Use unique barcode to avoid conflicts
        unique_barcode = f"WHISKEY{uuid4().hex[:8]}"
        item_data = {
            "name": "Test Whiskey",
            "category": "spirits",
            "barcode": unique_barcode,
            "sku": "WHISKEY001",
            "description": "Premium whiskey",
            "unit_of_measure": "bottle",
            "cost_per_unit": 35.00,
            "selling_price": 65.00,
            "par_level": 8.0,
            "reorder_point": 3.0,
            "expiration_days": 730.0
        }
        
        response = client.post("/api/v1/inventory/items", json=item_data)
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        assert response.status_code == 201
        
        item = response.json()
        assert item["name"] == "Test Whiskey"
        assert item["category"] == "spirits"
        assert item["barcode"] == unique_barcode
        
        # Clean up
        app.dependency_overrides.clear()

    def test_create_inventory_item_duplicate_barcode(self, test_item, mock_manager_user):
        """Test creating item with duplicate barcode"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        item_data = {
            "name": "Another Vodka",
            "category": "spirits",
            "barcode": "123456789",  # Same as test_item
            "unit_of_measure": "bottle"
        }
        
        response = client.post("/api/v1/inventory/items", json=item_data)
        assert response.status_code == 400
        assert "barcode already exists" in response.json()["detail"]
        
        # Clean up
        app.dependency_overrides.clear()

    def test_update_inventory_item(self, test_item, mock_manager_user):
        """Test updating inventory item"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        update_data = {
            "name": "Updated Vodka",
            "cost_per_unit": 30.00,
            "selling_price": 50.00
        }
        
        response = client.put(f"/api/v1/inventory/items/{test_item.id}", json=update_data)
        assert response.status_code == 200
        
        item = response.json()
        assert item["name"] == "Updated Vodka"
        assert float(item["cost_per_unit"]) == 30.00
        
        # Clean up
        app.dependency_overrides.clear()

    def test_update_inventory_item_not_found(self, mock_manager_user):
        """Test updating non-existent item"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        fake_id = str(uuid4())
        update_data = {"name": "Non-existent Item"}
        
        response = client.put(f"/api/v1/inventory/items/{fake_id}", json=update_data)
        assert response.status_code == 404
        
        # Clean up
        app.dependency_overrides.clear()

    def test_delete_inventory_item(self, test_item, mock_admin_user):
        """Test deleting inventory item (admin only)"""
        app.dependency_overrides[get_current_user] = lambda: mock_admin_user
        
        response = client.delete(f"/api/v1/inventory/items/{test_item.id}")
        assert response.status_code == 204
        
        # Verify item is soft deleted
        response = client.get(f"/api/v1/inventory/items/{test_item.id}")
        assert response.status_code == 404
        
        # Clean up
        app.dependency_overrides.clear()

    def test_search_inventory_items(self, test_item, mock_manager_user):
        """Test searching inventory items"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        response = client.get("/api/v1/inventory/items/search?q=vodka")
        assert response.status_code == 200
        
        items = response.json()
        assert len(items) >= 1
        assert any("vodka" in item["name"].lower() for item in items)
        
        # Clean up
        app.dependency_overrides.clear()

    def test_search_inventory_items_by_barcode(self, test_item, mock_manager_user):
        """Test searching by barcode"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        response = client.get("/api/v1/inventory/items/search?q=123456789")
        assert response.status_code == 200
        
        items = response.json()
        assert len(items) >= 1
        assert any(item["barcode"] == "123456789" for item in items)
        
        # Clean up
        app.dependency_overrides.clear()


class TestBarcodeScanning:
    """Test barcode scanning functionality"""

    def test_scan_barcode_success(self, test_item, test_location, test_stock_level, mock_bartender_user):
        """Test successful barcode scan"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        response = client.post(f"/api/v1/inventory/scan?barcode=123456789&location_id={test_location.id}")
        assert response.status_code == 200
        
        result = response.json()
        assert "item" in result
        assert result["item"]["name"] == "Test Vodka"
        assert "stock" in result
        assert result["stock"]["current_stock"] == 8.0
        
        # Clean up
        app.dependency_overrides.clear()

    def test_scan_barcode_not_found(self, mock_bartender_user):
        """Test scanning non-existent barcode"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        response = client.post("/api/v1/inventory/scan?barcode=nonexistent")
        assert response.status_code == 404
        assert "Item not found" in response.json()["detail"]
        
        # Clean up
        app.dependency_overrides.clear()


class TestStockLevels:
    """Test stock level management"""

    def test_get_stock_by_location(self, test_stock_level, test_location, mock_bartender_user):
        """Test getting stock levels by location"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        response = client.get(f"/api/v1/inventory/stock/location/{test_location.id}")
        assert response.status_code == 200
        
        stocks = response.json()
        assert len(stocks) >= 1
        assert any(stock["current_stock"] == 8.0 for stock in stocks)
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_stock_by_item(self, test_stock_level, test_item, mock_bartender_user):
        """Test getting stock levels by item"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        response = client.get(f"/api/v1/inventory/stock/item/{test_item.id}")
        assert response.status_code == 200
        
        stocks = response.json()
        assert len(stocks) >= 1
        assert any(stock["current_stock"] == 8.0 for stock in stocks)
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_specific_stock_level(self, test_stock_level, test_item, test_location, mock_bartender_user):
        """Test getting specific stock level"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        response = client.get(f"/api/v1/inventory/stock/{test_item.id}/{test_location.id}")
        assert response.status_code == 200
        
        stock = response.json()
        assert stock["current_stock"] == 8.0
        assert stock["reserved_stock"] == 1.0
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_stock_level_not_found(self, test_item, mock_bartender_user):
        """Test getting non-existent stock level"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        fake_location_id = str(uuid4())
        response = client.get(f"/api/v1/inventory/stock/{test_item.id}/{fake_location_id}")
        assert response.status_code == 404
        
        # Clean up
        app.dependency_overrides.clear()

    def test_update_stock_level(self, test_item, test_location, mock_bartender_user):
        """Test updating stock level"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        stock_data = {
            "item_id": str(test_item.id),
            "location_id": str(test_location.id),
            "current_stock": 15.0,
            "reserved_stock": 2.0
        }
        
        response = client.put(
            f"/api/v1/inventory/stock/{test_item.id}/{test_location.id}",
            json=stock_data
        )
        assert response.status_code == 200
        
        stock = response.json()
        assert stock["current_stock"] == 15.0
        assert stock["reserved_stock"] == 2.0
        
        # Clean up
        app.dependency_overrides.clear()

    def test_adjust_stock_positive(self, test_stock_level, test_item, test_location, mock_bartender_user):
        """Test positive stock adjustment"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        response = client.post(
            f"/api/v1/inventory/adjust/{test_item.id}/{test_location.id}?quantity_change=5.0&notes=Received shipment"
        )
        assert response.status_code == 200
        
        stock = response.json()
        assert stock["current_stock"] == 13.0  # 8.0 + 5.0
        
        # Clean up
        app.dependency_overrides.clear()

    def test_adjust_stock_negative(self, test_stock_level, test_item, test_location, mock_bartender_user):
        """Test negative stock adjustment"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        response = client.post(
            f"/api/v1/inventory/adjust/{test_item.id}/{test_location.id}?quantity_change=-3.0&notes=Sale"
        )
        assert response.status_code == 200
        
        stock = response.json()
        assert stock["current_stock"] == 5.0  # 8.0 - 3.0
        
        # Clean up
        app.dependency_overrides.clear()

    def test_adjust_stock_item_not_found(self, test_location, mock_bartender_user):
        """Test adjusting stock for non-existent item"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        fake_item_id = str(uuid4())
        response = client.post(
            f"/api/v1/inventory/adjust/{fake_item_id}/{test_location.id}?quantity_change=1.0"
        )
        assert response.status_code == 404
        
        # Clean up
        app.dependency_overrides.clear()


class TestLowStockAlerts:
    """Test low stock alert functionality"""

    def test_get_low_stock_alerts(self, db_session, test_location, mock_manager_user):
        """Test getting low stock alerts"""
        # Create item with low stock
        low_stock_item = InventoryItem(
            name="Low Stock Item",
            category=ItemCategory.SPIRITS,
            unit_of_measure=UnitOfMeasure.BOTTLE,
            par_level=10.0,
            reorder_point=5.0,
            is_active="true"
        )
        db_session.add(low_stock_item)
        db_session.commit()
        
        # Create stock level below reorder point
        low_stock = StockLevel(
            item_id=low_stock_item.id,
            location_id=test_location.id,
            current_stock=3.0  # Below reorder point of 5.0
        )
        db_session.add(low_stock)
        db_session.commit()
        
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        response = client.get("/api/v1/inventory/alerts/low-stock")
        assert response.status_code == 200
        
        alerts = response.json()
        assert len(alerts) >= 1
        assert any(alert["item"]["name"] == "Low Stock Item" for alert in alerts)
        
        # Clean up
        app.dependency_overrides.clear()

    def test_get_low_stock_alerts_by_location(self, db_session, test_location, mock_manager_user):
        """Test getting low stock alerts filtered by location"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        response = client.get(f"/api/v1/inventory/alerts/low-stock?location_id={test_location.id}")
        assert response.status_code == 200
        
        alerts = response.json()
        # Should return alerts only for the specified location
        for alert in alerts:
            assert alert["stock"]["location_id"] == str(test_location.id)
        
        # Clean up
        app.dependency_overrides.clear()


class TestPermissions:
    """Test role-based access control"""

    def test_create_item_insufficient_permissions(self, mock_barback_user):
        """Test that barback cannot create items"""
        app.dependency_overrides[get_current_user] = lambda: mock_barback_user
        
        item_data = {
            "name": "Unauthorized Item",
            "category": "spirits",
            "unit_of_measure": "bottle"
        }
        
        response = client.post("/api/v1/inventory/items", json=item_data)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
        
        # Clean up
        app.dependency_overrides.clear()

    def test_update_item_insufficient_permissions(self, test_item, mock_barback_user):
        """Test that barback cannot update items"""
        app.dependency_overrides[get_current_user] = lambda: mock_barback_user
        
        update_data = {"name": "Unauthorized Update"}
        
        response = client.put(f"/api/v1/inventory/items/{test_item.id}", json=update_data)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
        
        # Clean up
        app.dependency_overrides.clear()

    def test_delete_item_insufficient_permissions(self, test_item, mock_manager_user):
        """Test that manager cannot delete items (admin only)"""
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        response = client.delete(f"/api/v1/inventory/items/{test_item.id}")
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
        
        # Clean up
        app.dependency_overrides.clear()

    def test_stock_adjustment_permissions(self, test_stock_level, test_item, test_location, mock_barback_user):
        """Test that barback can adjust stock"""
        app.dependency_overrides[get_current_user] = lambda: mock_barback_user
        
        response = client.post(
            f"/api/v1/inventory/adjust/{test_item.id}/{test_location.id}?quantity_change=1.0&notes=Count adjustment"
        )
        assert response.status_code == 200
        
        # Clean up
        app.dependency_overrides.clear()


class TestMultiLocationInventory:
    """Test multi-location inventory tracking"""

    def test_multi_location_stock_tracking(self, db_session, test_item, mock_manager_user):
        """Test tracking inventory across multiple locations"""
        # Create additional locations
        rooftop = Location(
            name="Rooftop Bar",
            type=LocationType.ROOFTOP,
            is_active=True
        )
        storage = Location(
            name="Storage Room",
            type=LocationType.STORAGE,
            is_active=True
        )
        db_session.add_all([rooftop, storage])
        db_session.commit()
        
        # Create stock levels for different locations
        rooftop_stock = StockLevel(
            item_id=test_item.id,
            location_id=rooftop.id,
            current_stock=12.0
        )
        storage_stock = StockLevel(
            item_id=test_item.id,
            location_id=storage.id,
            current_stock=50.0
        )
        db_session.add_all([rooftop_stock, storage_stock])
        db_session.commit()
        
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        # Get stock levels for the item across all locations
        response = client.get(f"/api/v1/inventory/stock/item/{test_item.id}")
        assert response.status_code == 200
        
        stocks = response.json()
        assert len(stocks) >= 3  # Main bar, rooftop, storage
        
        location_stocks = {stock["location_id"]: stock["current_stock"] for stock in stocks}
        assert str(rooftop.id) in location_stocks
        assert str(storage.id) in location_stocks
        assert location_stocks[str(rooftop.id)] == 12.0
        assert location_stocks[str(storage.id)] == 50.0
        
        # Clean up
        app.dependency_overrides.clear()


class TestAuditLogging:
    """Test audit logging for inventory adjustments"""

    def test_adjustment_creates_transaction_record(self, db_session, test_stock_level, test_item, test_location, mock_bartender_user):
        """Test that stock adjustments create transaction records"""
        app.dependency_overrides[get_current_user] = lambda: mock_bartender_user
        
        # Make adjustment
        response = client.post(
            f"/api/v1/inventory/adjust/{test_item.id}/{test_location.id}?quantity_change=2.0&transaction_type=adjustment&notes=Manual count adjustment"
        )
        assert response.status_code == 200
        
        # Verify transaction record was created
        transaction = db_session.query(Transaction).filter(
            Transaction.item_id == test_item.id,
            Transaction.location_id == test_location.id,
            Transaction.transaction_type == TransactionType.ADJUSTMENT,
            Transaction.quantity == 2.0
        ).first()
        
        assert transaction is not None
        assert transaction.notes == "Manual count adjustment"
        assert transaction.user_id == mock_bartender_user.id
        
        # Clean up
        app.dependency_overrides.clear()


class TestStockThresholdAlerts:
    """Test configurable threshold alerts"""

    def test_low_stock_threshold_detection(self, db_session, test_location, mock_manager_user):
        """Test that items below reorder point are detected"""
        # Create item with specific thresholds
        threshold_item = InventoryItem(
            name="Threshold Test Item",
            category=ItemCategory.BEER,
            unit_of_measure=UnitOfMeasure.BOTTLE,
            par_level=24.0,
            reorder_point=6.0,  # Reorder when below 6 bottles
            is_active="true"
        )
        db_session.add(threshold_item)
        db_session.commit()
        
        # Create stock level below threshold
        low_stock = StockLevel(
            item_id=threshold_item.id,
            location_id=test_location.id,
            current_stock=4.0  # Below reorder point
        )
        db_session.add(low_stock)
        db_session.commit()
        
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        response = client.get("/api/v1/inventory/alerts/low-stock")
        assert response.status_code == 200
        
        alerts = response.json()
        threshold_alert = next(
            (alert for alert in alerts if alert["item"]["name"] == "Threshold Test Item"),
            None
        )
        
        assert threshold_alert is not None
        assert threshold_alert["stock"]["current_stock"] == 4.0
        assert threshold_alert["shortage"] == 2.0  # 6.0 - 4.0
        
        # Clean up
        app.dependency_overrides.clear()

    def test_stock_above_threshold_not_alerted(self, db_session, test_location, mock_manager_user):
        """Test that items above reorder point are not in alerts"""
        # Create item with stock above threshold
        good_stock_item = InventoryItem(
            name="Good Stock Item",
            category=ItemCategory.WINE,
            unit_of_measure=UnitOfMeasure.BOTTLE,
            par_level=12.0,
            reorder_point=3.0,
            is_active="true"
        )
        db_session.add(good_stock_item)
        db_session.commit()
        
        # Create stock level above threshold
        good_stock = StockLevel(
            item_id=good_stock_item.id,
            location_id=test_location.id,
            current_stock=8.0  # Above reorder point
        )
        db_session.add(good_stock)
        db_session.commit()
        
        app.dependency_overrides[get_current_user] = lambda: mock_manager_user
        
        response = client.get("/api/v1/inventory/alerts/low-stock")
        assert response.status_code == 200
        
        alerts = response.json()
        good_stock_alert = next(
            (alert for alert in alerts if alert["item"]["name"] == "Good Stock Item"),
            None
        )
        
        # Should not be in alerts
        assert good_stock_alert is None
        
        # Clean up
        app.dependency_overrides.clear()