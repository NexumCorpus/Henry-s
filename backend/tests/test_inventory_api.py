import pytest
from uuid import uuid4
from app.core.dependencies import get_current_user
from app.models.location import Location, LocationType
from app.models.inventory import InventoryItem, ItemCategory, UnitOfMeasure, StockLevel
from app.schemas.user import UserResponse


@pytest.fixture
def mock_current_user():
    return UserResponse(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        role="manager",
        is_active=True
    )


@pytest.fixture
def test_location(db_session):
    location = Location(
        name="Main Bar",
        type=LocationType.BAR,
        description="Main bar area"
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location


@pytest.fixture
def test_item(db_session):
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
    db_session.refresh(item)
    return item


@pytest.fixture
def test_stock_level(db_session, test_item, test_location):
    stock = StockLevel(
        item_id=test_item.id,
        location_id=test_location.id,
        current_stock=8.0
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    return stock


class TestInventoryItems:
    def test_get_inventory_items(self, client, test_item, mock_current_user):
        # Override the current user dependency
        client.app.dependency_overrides[get_current_user] = lambda: mock_current_user
        
        response = client.get("/api/v1/inventory/items")
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 1
        assert any(item["name"] == "Test Vodka" for item in items)

    def test_get_inventory_item_by_id(self, test_item):
        response = client.get(f"/api/v1/inventory/items/{test_item.id}")
        assert response.status_code == 200
        item = response.json()
        assert item["name"] == "Test Vodka"
        assert item["category"] == "spirits"

    def test_get_inventory_item_not_found(self):
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/inventory/items/{fake_id}")
        assert response.status_code == 404

    def test_create_inventory_item(self):
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
        assert item["barcode"] == "987654321"

    def test_create_inventory_item_duplicate_barcode(self, test_item):
        item_data = {
            "name": "Another Vodka",
            "category": "spirits",
            "barcode": "123456789",  # Same as test_item
            "unit_of_measure": "bottle"
        }
        response = client.post("/api/v1/inventory/items", json=item_data)
        assert response.status_code == 400
        assert "barcode already exists" in response.json()["detail"]

    def test_update_inventory_item(self, test_item):
        update_data = {
            "name": "Updated Vodka",
            "cost_per_unit": 30.00
        }
        response = client.put(f"/api/v1/inventory/items/{test_item.id}", json=update_data)
        assert response.status_code == 200
        item = response.json()
        assert item["name"] == "Updated Vodka"
        assert float(item["cost_per_unit"]) == 30.00

    def test_update_inventory_item_not_found(self):
        fake_id = str(uuid4())
        update_data = {"name": "Non-existent Item"}
        response = client.put(f"/api/v1/inventory/items/{fake_id}", json=update_data)
        assert response.status_code == 404

    def test_delete_inventory_item(self, test_item):
        # Override current user to admin for delete permission
        def override_admin_user():
            return UserResponse(
                id=uuid4(),
                username="admin",
                email="admin@example.com",
                role="admin",
                is_active=True
            )
        
        app.dependency_overrides[get_current_user] = override_admin_user
        
        response = client.delete(f"/api/v1/inventory/items/{test_item.id}")
        assert response.status_code == 204
        
        # Verify item is soft deleted
        get_response = client.get(f"/api/v1/inventory/items/{test_item.id}")
        assert get_response.status_code == 404

    def test_search_inventory_items(self, test_item):
        response = client.get("/api/v1/inventory/items/search?q=vodka")
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 1
        assert any("vodka" in item["name"].lower() for item in items)

    def test_search_inventory_items_by_barcode(self, test_item):
        response = client.get("/api/v1/inventory/items/search?q=123456789")
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 1
        assert any(item["barcode"] == "123456789" for item in items)


class TestBarcodeScanning:
    def test_scan_barcode_success(self, test_item, test_location):
        response = client.post(f"/api/v1/inventory/scan?barcode=123456789&location_id={test_location.id}")
        assert response.status_code == 200
        result = response.json()
        assert "item" in result
        assert result["item"]["name"] == "Test Vodka"

    def test_scan_barcode_not_found(self):
        response = client.post("/api/v1/inventory/scan?barcode=nonexistent")
        assert response.status_code == 404


class TestStockLevels:
    def test_get_stock_by_location(self, test_stock_level, test_location):
        response = client.get(f"/api/v1/inventory/stock/location/{test_location.id}")
        assert response.status_code == 200
        stocks = response.json()
        assert len(stocks) >= 1
        assert any(stock["current_stock"] == 8.0 for stock in stocks)

    def test_get_stock_by_item(self, test_stock_level, test_item):
        response = client.get(f"/api/v1/inventory/stock/item/{test_item.id}")
        assert response.status_code == 200
        stocks = response.json()
        assert len(stocks) >= 1
        assert any(stock["current_stock"] == 8.0 for stock in stocks)

    def test_get_specific_stock_level(self, test_stock_level, test_item, test_location):
        response = client.get(f"/api/v1/inventory/stock/{test_item.id}/{test_location.id}")
        assert response.status_code == 200
        stock = response.json()
        assert stock["current_stock"] == 8.0

    def test_get_stock_level_not_found(self, test_item):
        fake_location_id = str(uuid4())
        response = client.get(f"/api/v1/inventory/stock/{test_item.id}/{fake_location_id}")
        assert response.status_code == 404

    def test_update_stock_level(self, test_item, test_location):
        stock_data = {
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

    def test_adjust_stock_positive(self, test_stock_level, test_item, test_location):
        response = client.post(
            f"/api/v1/inventory/adjust/{test_item.id}/{test_location.id}?quantity_change=5.0&notes=Received shipment"
        )
        assert response.status_code == 200
        stock = response.json()
        assert stock["current_stock"] == 13.0  # 8.0 + 5.0

    def test_adjust_stock_negative(self, test_stock_level, test_item, test_location):
        response = client.post(
            f"/api/v1/inventory/adjust/{test_item.id}/{test_location.id}?quantity_change=-3.0&notes=Sale"
        )
        assert response.status_code == 200
        stock = response.json()
        assert stock["current_stock"] == 5.0  # 8.0 - 3.0

    def test_adjust_stock_item_not_found(self, test_location):
        fake_item_id = str(uuid4())
        response = client.post(
            f"/api/v1/inventory/adjust/{fake_item_id}/{test_location.id}?quantity_change=1.0"
        )
        assert response.status_code == 404


class TestLowStockAlerts:
    def test_get_low_stock_alerts(self, test_stock_level, test_item, test_location):
        # Current stock is 8.0, reorder point is 5.0, so this should not be in low stock
        response = client.get("/api/v1/inventory/alerts/low-stock")
        assert response.status_code == 200
        alerts = response.json()
        
        # Adjust stock to below reorder point
        client.post(
            f"/api/v1/inventory/adjust/{test_item.id}/{test_location.id}?quantity_change=-5.0"
        )
        
        # Now check for low stock alerts
        response = client.get("/api/v1/inventory/alerts/low-stock")
        assert response.status_code == 200
        alerts = response.json()
        assert len(alerts) >= 1
        assert any(alert["item"]["name"] == "Test Vodka" for alert in alerts)

    def test_get_low_stock_alerts_by_location(self, test_location):
        response = client.get(f"/api/v1/inventory/alerts/low-stock?location_id={test_location.id}")
        assert response.status_code == 200
        alerts = response.json()
        assert isinstance(alerts, list)


class TestPermissions:
    def test_create_item_insufficient_permissions(self):
        # Override current user to barback (insufficient permissions)
        def override_barback_user():
            return UserResponse(
                id=uuid4(),
                username="barback",
                email="barback@example.com",
                role="barback",
                is_active=True
            )
        
        app.dependency_overrides[get_current_user] = override_barback_user
        
        item_data = {
            "name": "Unauthorized Item",
            "category": "spirits",
            "unit_of_measure": "bottle"
        }
        response = client.post("/api/v1/inventory/items", json=item_data)
        assert response.status_code == 403

    def test_update_item_insufficient_permissions(self, test_item):
        # Override current user to barback (insufficient permissions)
        def override_barback_user():
            return UserResponse(
                id=uuid4(),
                username="barback",
                email="barback@example.com",
                role="barback",
                is_active=True
            )
        
        app.dependency_overrides[get_current_user] = override_barback_user
        
        update_data = {"name": "Unauthorized Update"}
        response = client.put(f"/api/v1/inventory/items/{test_item.id}", json=update_data)
        assert response.status_code == 403

    def test_delete_item_insufficient_permissions(self, test_item):
        # Override current user to manager (insufficient permissions for delete)
        def override_manager_user():
            return UserResponse(
                id=uuid4(),
                username="manager",
                email="manager@example.com",
                role="manager",
                is_active=True
            )
        
        app.dependency_overrides[get_current_user] = override_manager_user
        
        response = client.delete(f"/api/v1/inventory/items/{test_item.id}")
        assert response.status_code == 403


# Cleanup
def teardown_module():
    Base.metadata.drop_all(bind=engine)