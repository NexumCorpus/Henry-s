import pytest
import base64
import io
from PIL import Image, ImageDraw, ImageFont
from unittest.mock import Mock, patch
from app.services.barcode import BarcodeService
from app.models.inventory import InventoryItem, ItemCategory, UnitOfMeasure
from app.models.location import Location
from app.models.inventory import StockLevel
import uuid


class TestBarcodeService:
    """Test barcode scanning functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def barcode_service(self, mock_db):
        """Create barcode service instance"""
        return BarcodeService(mock_db)
    
    @pytest.fixture
    def sample_item(self):
        """Create sample inventory item"""
        return InventoryItem(
            id=uuid.uuid4(),
            name="Test Vodka",
            category=ItemCategory.SPIRITS,
            barcode="1234567890123",
            unit_of_measure=UnitOfMeasure.BOTTLE,
            par_level=10.0,
            reorder_point=5.0,
            cost_per_unit=25.00,
            selling_price=8.00,
            is_active="true"
        )
    
    def create_test_image_with_barcode(self, barcode_text: str = "1234567890123") -> str:
        """Create a test image with barcode-like pattern and return as base64"""
        # Create a simple image with text (simulating a barcode)
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw barcode-like vertical lines
        for i in range(0, 300, 10):
            if i % 20 == 0:
                draw.rectangle([i, 20, i+5, 80], fill='black')
        
        # Add barcode text
        draw.text((50, 85), barcode_text, fill='black')
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    def test_decode_base64_image_success(self, barcode_service):
        """Test successful base64 image decoding"""
        base64_image = self.create_test_image_with_barcode()
        
        image = barcode_service.decode_base64_image(base64_image)
        
        assert image is not None
        assert isinstance(image, Image.Image)
        assert image.size == (300, 100)
    
    def test_decode_base64_image_with_data_url(self, barcode_service):
        """Test base64 image decoding with data URL prefix"""
        base64_image = self.create_test_image_with_barcode()
        data_url = f"data:image/png;base64,{base64_image}"
        
        image = barcode_service.decode_base64_image(data_url)
        
        assert image is not None
        assert isinstance(image, Image.Image)
    
    def test_decode_base64_image_invalid(self, barcode_service):
        """Test base64 image decoding with invalid data"""
        invalid_base64 = "invalid_base64_data"
        
        image = barcode_service.decode_base64_image(invalid_base64)
        
        assert image is None
    
    def test_validate_barcode_format_upc_a(self, barcode_service):
        """Test UPC-A barcode format validation"""
        result = barcode_service.validate_barcode_format("123456789012")
        
        assert result["valid"] is True
        assert result["format"] == "UPC-A"
        assert result["length"] == 12
    
    def test_validate_barcode_format_ean_13(self, barcode_service):
        """Test EAN-13 barcode format validation"""
        result = barcode_service.validate_barcode_format("1234567890123")
        
        assert result["valid"] is True
        assert result["format"] == "EAN-13"
        assert result["length"] == 13
    
    def test_validate_barcode_format_ean_8(self, barcode_service):
        """Test EAN-8 barcode format validation"""
        result = barcode_service.validate_barcode_format("12345678")
        
        assert result["valid"] is True
        assert result["format"] == "EAN-8"
        assert result["length"] == 8
    
    def test_validate_barcode_format_code_128(self, barcode_service):
        """Test Code 128 barcode format validation"""
        result = barcode_service.validate_barcode_format("ABC123")
        
        assert result["valid"] is True
        assert result["format"] == "Code 128"
        assert result["length"] == 6
    
    def test_validate_barcode_format_invalid(self, barcode_service):
        """Test invalid barcode format"""
        result = barcode_service.validate_barcode_format("")
        
        assert result["valid"] is False
        assert "error" in result
    
    @patch('app.services.barcode.pyzbar.decode')
    def test_scan_barcodes_from_image_success(self, mock_decode, barcode_service):
        """Test successful barcode scanning from image"""
        # Mock pyzbar response
        mock_barcode = Mock()
        mock_barcode.data = b'1234567890123'
        mock_barcode.type = 'EAN13'
        mock_barcode.rect = Mock()
        mock_decode.return_value = [mock_barcode]
        
        image = Image.new('RGB', (300, 100), color='white')
        result = barcode_service.scan_barcodes_from_image(image)
        
        assert len(result) == 1
        assert result[0]['data'] == '1234567890123'
        assert result[0]['type'] == 'EAN13'
        assert result[0]['method'] == 'original'
    
    @patch('app.services.barcode.pyzbar.decode')
    def test_scan_barcodes_from_image_no_barcode(self, mock_decode, barcode_service):
        """Test barcode scanning when no barcode is found"""
        mock_decode.return_value = []
        
        image = Image.new('RGB', (300, 100), color='white')
        result = barcode_service.scan_barcodes_from_image(image)
        
        assert len(result) == 0
    
    @patch('app.services.barcode.BarcodeService.scan_barcodes_from_image')
    @patch('app.services.barcode.BarcodeService.decode_base64_image')
    def test_scan_barcode_from_base64_success(self, mock_decode, mock_scan, barcode_service, sample_item):
        """Test successful barcode scanning from base64 image"""
        # Mock image decoding
        mock_image = Image.new('RGB', (300, 100), color='white')
        mock_decode.return_value = mock_image
        
        # Mock barcode scanning
        mock_scan.return_value = [{
            'data': '1234567890123',
            'type': 'EAN13',
            'rect': Mock(),
            'method': 'original'
        }]
        
        # Mock inventory service
        barcode_service.inventory_service.get_item_by_barcode = Mock(return_value=sample_item)
        barcode_service.inventory_service.get_stock_level = Mock(return_value=None)
        
        result = barcode_service.scan_barcode_from_base64("fake_base64")
        
        assert result["success"] is True
        assert result["barcode"] == "1234567890123"
        assert result["item"]["name"] == "Test Vodka"
        assert result["item"]["category"] == ItemCategory.SPIRITS
    
    @patch('app.services.barcode.BarcodeService.scan_barcodes_from_image')
    @patch('app.services.barcode.BarcodeService.decode_base64_image')
    def test_scan_barcode_from_base64_item_not_found(self, mock_decode, mock_scan, barcode_service):
        """Test barcode scanning when item is not found"""
        # Mock image decoding
        mock_image = Image.new('RGB', (300, 100), color='white')
        mock_decode.return_value = mock_image
        
        # Mock barcode scanning
        mock_scan.return_value = [{
            'data': '1234567890123',
            'type': 'EAN13',
            'rect': Mock(),
            'method': 'original'
        }]
        
        # Mock inventory service - item not found
        barcode_service.inventory_service.get_item_by_barcode = Mock(return_value=None)
        barcode_service._get_similar_items = Mock(return_value=[])
        
        result = barcode_service.scan_barcode_from_base64("fake_base64")
        
        assert "error" in result
        assert result["error"] == "Item not found"
        assert result["barcode"] == "1234567890123"
    
    @patch('app.services.barcode.BarcodeService.scan_barcodes_from_image')
    @patch('app.services.barcode.BarcodeService.decode_base64_image')
    def test_scan_barcode_from_base64_no_barcode_found(self, mock_decode, mock_scan, barcode_service):
        """Test barcode scanning when no barcode is detected in image"""
        # Mock image decoding
        mock_image = Image.new('RGB', (300, 100), color='white')
        mock_decode.return_value = mock_image
        
        # Mock barcode scanning - no barcodes found
        mock_scan.return_value = []
        
        result = barcode_service.scan_barcode_from_base64("fake_base64")
        
        assert "error" in result
        assert result["error"] == "No barcode found in image"
    
    def test_scan_barcode_from_base64_invalid_image(self, barcode_service):
        """Test barcode scanning with invalid base64 image"""
        result = barcode_service.scan_barcode_from_base64("invalid_base64")
        
        assert "error" in result
        assert "Failed to decode image" in result["error"]
    
    @patch('app.services.barcode.BarcodeService.scan_barcodes_from_image')
    @patch('app.services.barcode.BarcodeService.decode_base64_image')
    def test_scan_barcode_with_stock_info(self, mock_decode, mock_scan, barcode_service, sample_item):
        """Test barcode scanning with stock level information"""
        location_id = uuid.uuid4()
        
        # Mock image decoding
        mock_image = Image.new('RGB', (300, 100), color='white')
        mock_decode.return_value = mock_image
        
        # Mock barcode scanning
        mock_scan.return_value = [{
            'data': '1234567890123',
            'type': 'EAN13',
            'rect': Mock(),
            'method': 'original'
        }]
        
        # Mock stock level
        mock_stock = Mock()
        mock_stock.current_stock = 3.0
        mock_stock.reserved_stock = 0.0
        mock_stock.last_updated = Mock()
        mock_stock.last_updated.isoformat.return_value = "2023-01-01T00:00:00"
        
        # Mock inventory service
        barcode_service.inventory_service.get_item_by_barcode = Mock(return_value=sample_item)
        barcode_service.inventory_service.get_stock_level = Mock(return_value=mock_stock)
        
        result = barcode_service.scan_barcode_from_base64("fake_base64", location_id)
        
        assert result["success"] is True
        assert result["stock"] is not None
        assert result["stock"]["current_stock"] == 3.0
        assert result["stock"]["below_reorder_point"] is True  # 3.0 <= 5.0 (reorder point)
    
    def test_get_similar_items(self, barcode_service, mock_db):
        """Test getting similar items for unknown barcode"""
        # Mock database query
        mock_item = Mock()
        mock_item.id = uuid.uuid4()
        mock_item.name = "Similar Vodka"
        mock_item.barcode = "1234567890124"  # Similar barcode
        mock_item.sku = "SKU123"
        mock_item.category = ItemCategory.SPIRITS
        
        mock_query = Mock()
        mock_query.filter.return_value.limit.return_value.all.return_value = [mock_item]
        mock_db.query.return_value = mock_query
        
        result = barcode_service._get_similar_items("1234567890123")
        
        assert len(result) == 1
        assert result[0]["name"] == "Similar Vodka"
        assert result[0]["barcode"] == "1234567890124"


class TestBarcodeIntegration:
    """Integration tests for barcode scanning with real database"""
    
    @pytest.mark.asyncio
    async def test_barcode_scanning_accuracy(self):
        """Test barcode scanning accuracy with various image conditions"""
        # This would be implemented with real test images
        # For now, we'll mark it as a placeholder
        pass
    
    @pytest.mark.asyncio
    async def test_barcode_scanning_performance(self):
        """Test barcode scanning performance under load"""
        # This would test scanning multiple images concurrently
        pass
    
    @pytest.mark.asyncio
    async def test_barcode_scanning_edge_cases(self):
        """Test barcode scanning with edge cases like rotated images, poor lighting"""
        # This would test various image preprocessing scenarios
        pass