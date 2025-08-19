import pytest
import json
import base64
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.models.inventory import ItemCategory, UnitOfMeasure
from app.models.transaction import TransactionType
import uuid


class TestMobileAPI:
    """Test mobile-optimized API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer test_token"}
    
    @pytest.fixture
    def sample_barcode_image(self):
        """Create sample base64 encoded image"""
        # Create a simple 1x1 pixel PNG image
        import io
        from PIL import Image
        
        img = Image.new('RGB', (1, 1), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.barcode.BarcodeService.scan_barcode_from_base64')
    def test_scan_barcode_image_success(self, mock_scan, mock_user, client, auth_headers, sample_barcode_image):
        """Test successful barcode scanning from base64 image"""
        # Mock user
        mock_user.return_value = Mock(id=uuid.uuid4())
        
        # Mock barcode scan result
        mock_scan.return_value = {
            "success": True,
            "barcode": "1234567890123",
            "item": {
                "id": str(uuid.uuid4()),
                "name": "Test Vodka",
                "category": "spirits"
            }
        }
        
        request_data = {
            "image_data": sample_barcode_image,
            "location_id": str(uuid.uuid4())
        }
        
        response = client.post(
            "/api/v1/mobile/scan/barcode",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["barcode"] == "1234567890123"
        assert data["item"]["name"] == "Test Vodka"
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.barcode.BarcodeService.scan_barcode_from_base64')
    def test_scan_barcode_image_not_found(self, mock_scan, mock_user, client, auth_headers, sample_barcode_image):
        """Test barcode scanning when item is not found"""
        # Mock user
        mock_user.return_value = Mock(id=uuid.uuid4())
        
        # Mock barcode scan result - item not found
        mock_scan.return_value = {
            "error": "Item not found",
            "barcode": "1234567890123"
        }
        
        request_data = {
            "image_data": sample_barcode_image
        }
        
        response = client.post(
            "/api/v1/mobile/scan/barcode",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Item not found"
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.inventory.InventoryService.get_stock_levels_by_location')
    @patch('app.services.inventory.InventoryService.get_item')
    def test_get_quick_stock_overview(self, mock_get_item, mock_get_stock, mock_user, client, auth_headers):
        """Test getting quick stock overview for mobile"""
        location_id = uuid.uuid4()
        item_id = uuid.uuid4()
        
        # Mock user
        mock_user.return_value = Mock(id=uuid.uuid4())
        
        # Mock stock levels
        mock_stock = Mock()
        mock_stock.item_id = item_id
        mock_stock.current_stock = 8.0
        mock_stock.last_updated.isoformat.return_value = "2023-01-01T00:00:00"
        mock_get_stock.return_value = [mock_stock]
        
        # Mock item
        mock_item = Mock()
        mock_item.id = item_id
        mock_item.name = "Test Vodka"
        mock_item.category = ItemCategory.SPIRITS
        mock_item.unit_of_measure = UnitOfMeasure.BOTTLE
        mock_item.reorder_point = 5.0
        mock_item.par_level = 10.0
        mock_item.barcode = "1234567890123"
        mock_get_item.return_value = mock_item
        
        response = client.get(
            f"/api/v1/mobile/stock/quick/{location_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Vodka"
        assert data[0]["current_stock"] == 8.0
        assert data[0]["is_low_stock"] is False  # 8.0 > 5.0 (reorder point)
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.inventory.InventoryService.get_stock_level')
    @patch('app.services.inventory.InventoryService.adjust_stock')
    @patch('app.services.inventory.InventoryService.get_item')
    def test_quick_stock_update(self, mock_get_item, mock_adjust, mock_get_stock, mock_user, client, auth_headers):
        """Test quick stock update from mobile"""
        item_id = uuid.uuid4()
        location_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Mock user
        mock_user.return_value = Mock(id=user_id)
        
        # Mock current stock level
        mock_current_stock = Mock()
        mock_current_stock.current_stock = 5.0
        mock_get_stock.return_value = mock_current_stock
        
        # Mock updated stock level
        mock_updated_stock = Mock()
        mock_updated_stock.current_stock = 8.0
        mock_updated_stock.last_updated.isoformat.return_value = "2023-01-01T00:00:00"
        mock_adjust.return_value = mock_updated_stock
        
        # Mock item
        mock_item = Mock()
        mock_item.reorder_point = 3.0
        mock_item.name = "Test Vodka"
        mock_get_item.return_value = mock_item
        
        request_data = {
            "item_id": str(item_id),
            "location_id": str(location_id),
            "new_stock": 8.0,
            "transaction_type": "adjustment",
            "notes": "Mobile update"
        }
        
        response = client.post(
            "/api/v1/mobile/stock/quick-update",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["old_stock"] == 5.0
        assert data["new_stock"] == 8.0
        assert data["change"] == 3.0
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.inventory.InventoryService.get_stock_level')
    @patch('app.services.inventory.InventoryService.adjust_stock')
    @patch('app.services.inventory.InventoryService.get_item')
    def test_bulk_stock_update(self, mock_get_item, mock_adjust, mock_get_stock, mock_user, client, auth_headers):
        """Test bulk stock update from mobile"""
        item_id_1 = uuid.uuid4()
        item_id_2 = uuid.uuid4()
        location_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Mock user
        mock_user.return_value = Mock(id=user_id)
        
        # Mock current stock levels
        mock_current_stock_1 = Mock()
        mock_current_stock_1.current_stock = 5.0
        mock_current_stock_2 = Mock()
        mock_current_stock_2.current_stock = 3.0
        
        def mock_get_stock_side_effect(item_id, loc_id):
            if item_id == item_id_1:
                return mock_current_stock_1
            return mock_current_stock_2
        
        mock_get_stock.side_effect = mock_get_stock_side_effect
        
        # Mock updated stock levels
        mock_updated_stock_1 = Mock()
        mock_updated_stock_1.current_stock = 8.0
        mock_updated_stock_2 = Mock()
        mock_updated_stock_2.current_stock = 6.0
        
        def mock_adjust_side_effect(item_id, loc_id, change, user_id, trans_type, notes):
            if item_id == item_id_1:
                return mock_updated_stock_1
            return mock_updated_stock_2
        
        mock_adjust.side_effect = mock_adjust_side_effect
        
        # Mock items
        mock_item = Mock()
        mock_item.reorder_point = 2.0
        mock_item.name = "Test Item"
        mock_get_item.return_value = mock_item
        
        request_data = {
            "updates": [
                {
                    "item_id": str(item_id_1),
                    "location_id": str(location_id),
                    "new_stock": 8.0,
                    "transaction_type": "adjustment"
                },
                {
                    "item_id": str(item_id_2),
                    "location_id": str(location_id),
                    "new_stock": 6.0,
                    "transaction_type": "adjustment"
                }
            ]
        }
        
        response = client.post(
            "/api/v1/mobile/stock/bulk-update",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["successful_updates"] == 2
        assert data["failed_updates"] == 0
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.inventory.InventoryService.adjust_stock')
    def test_sync_offline_transactions(self, mock_adjust, mock_user, client, auth_headers):
        """Test syncing offline transactions from mobile"""
        item_id = uuid.uuid4()
        location_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Mock user
        mock_user.return_value = Mock(id=user_id)
        
        # Mock updated stock level
        mock_updated_stock = Mock()
        mock_updated_stock.current_stock = 7.0
        mock_updated_stock.last_updated.isoformat.return_value = "2023-01-01T00:00:00"
        mock_adjust.return_value = mock_updated_stock
        
        request_data = {
            "transactions": [
                {
                    "local_id": "local_123",
                    "item_id": str(item_id),
                    "location_id": str(location_id),
                    "quantity_change": -2.0,
                    "transaction_type": "sale",
                    "timestamp": 1640995200.0,  # 2022-01-01 00:00:00
                    "notes": "Offline sale"
                }
            ],
            "last_sync_timestamp": 1640991600.0  # 2021-12-31 23:00:00
        }
        
        response = client.post(
            "/api/v1/mobile/sync/offline",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["processed_count"] == 1
        assert data["failed_count"] == 0
        assert len(data["transactions"]["processed"]) == 1
        assert data["transactions"]["processed"][0]["local_id"] == "local_123"
    
    @patch('app.core.dependencies.get_current_user')
    def test_get_categories_mobile(self, mock_user, client, auth_headers):
        """Test getting item categories for mobile"""
        # Mock user
        mock_user.return_value = Mock(id=uuid.uuid4())
        
        response = client.get(
            "/api/v1/mobile/categories",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "spirits" in data
        assert "beer" in data
        assert "wine" in data
    
    @patch('app.core.dependencies.get_current_user')
    @patch('app.services.inventory.InventoryService.get_low_stock_items')
    def test_get_location_alerts(self, mock_get_low_stock, mock_user, client, auth_headers):
        """Test getting alerts for a location"""
        location_id = uuid.uuid4()
        item_id = uuid.uuid4()
        
        # Mock user
        mock_user.return_value = Mock(id=uuid.uuid4())
        
        # Mock low stock items
        mock_get_low_stock.return_value = [
            {
                "item_id": str(item_id),
                "item_name": "Low Stock Vodka",
                "current_stock": 2.0,
                "reorder_point": 5.0
            }
        ]
        
        response = client.get(
            f"/api/v1/mobile/locations/{location_id}/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "low_stock"
        assert data[0]["severity"] == "warning"
        assert data[0]["item_name"] == "Low Stock Vodka"
        assert data[0]["current_stock"] == 2.0
    
    def test_scan_barcode_file_invalid_content_type(self, client, auth_headers):
        """Test barcode scanning with invalid file type"""
        # Create a text file instead of image
        files = {"file": ("test.txt", "not an image", "text/plain")}
        
        with patch('app.core.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id=uuid.uuid4())
            
            response = client.post(
                "/api/v1/mobile/scan/barcode/file",
                files=files,
                headers=auth_headers
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "File must be an image" in data["detail"]
    
    def test_quick_stock_update_item_not_found(self, client, auth_headers):
        """Test quick stock update when item is not found"""
        item_id = uuid.uuid4()
        location_id = uuid.uuid4()
        
        request_data = {
            "item_id": str(item_id),
            "location_id": str(location_id),
            "new_stock": 8.0
        }
        
        with patch('app.core.dependencies.get_current_user') as mock_user:
            mock_user.return_value = Mock(id=uuid.uuid4())
            
            with patch('app.services.inventory.InventoryService.get_stock_level') as mock_get_stock:
                mock_get_stock.return_value = None
                
                with patch('app.services.inventory.InventoryService.adjust_stock') as mock_adjust:
                    mock_adjust.return_value = None
                    
                    response = client.post(
                        "/api/v1/mobile/stock/quick-update",
                        json=request_data,
                        headers=auth_headers
                    )
        
        assert response.status_code == 404
        data = response.json()
        assert "Item or location not found" in data["detail"]


class TestMobileAPIAuthentication:
    """Test mobile API authentication and authorization"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_scan_barcode_unauthorized(self, client):
        """Test barcode scanning without authentication"""
        request_data = {
            "image_data": "fake_base64"
        }
        
        response = client.post(
            "/api/v1/mobile/scan/barcode",
            json=request_data
        )
        
        assert response.status_code == 401
    
    def test_quick_stock_overview_unauthorized(self, client):
        """Test stock overview without authentication"""
        location_id = uuid.uuid4()
        
        response = client.get(f"/api/v1/mobile/stock/quick/{location_id}")
        
        assert response.status_code == 401
    
    def test_stock_update_unauthorized(self, client):
        """Test stock update without authentication"""
        request_data = {
            "item_id": str(uuid.uuid4()),
            "location_id": str(uuid.uuid4()),
            "new_stock": 8.0
        }
        
        response = client.post(
            "/api/v1/mobile/stock/quick-update",
            json=request_data
        )
        
        assert response.status_code == 401