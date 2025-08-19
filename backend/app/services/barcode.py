import io
import base64
from typing import Optional, Dict, Any, List
from PIL import Image
from pyzbar import pyzbar
import cv2
import numpy as np
from sqlalchemy.orm import Session
from app.services.inventory import InventoryService
from app.models.inventory import InventoryItem
from uuid import UUID


class BarcodeService:
    """Service for barcode and QR code scanning functionality"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)
    
    def decode_base64_image(self, base64_string: str) -> Optional[Image.Image]:
        """Decode base64 image string to PIL Image"""
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_string)
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            return image
        except Exception as e:
            print(f"Error decoding base64 image: {e}")
            return None
    
    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for better barcode detection"""
        # Convert PIL Image to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold to handle varying lighting
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def scan_barcodes_from_image(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Extract barcodes from image using multiple preprocessing techniques"""
        barcodes = []
        
        # Try scanning original image first
        original_barcodes = pyzbar.decode(image)
        for barcode in original_barcodes:
            barcodes.append({
                'data': barcode.data.decode('utf-8'),
                'type': barcode.type,
                'rect': barcode.rect,
                'method': 'original'
            })
        
        # If no barcodes found, try with preprocessing
        if not barcodes:
            preprocessed = self.preprocess_image(image)
            preprocessed_barcodes = pyzbar.decode(preprocessed)
            
            for barcode in preprocessed_barcodes:
                barcodes.append({
                    'data': barcode.data.decode('utf-8'),
                    'type': barcode.type,
                    'rect': barcode.rect,
                    'method': 'preprocessed'
                })
        
        return barcodes
    
    def scan_barcode_from_base64(self, base64_image: str, location_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Scan barcode from base64 encoded image and return item information"""
        try:
            # Decode image
            image = self.decode_base64_image(base64_image)
            if not image:
                return {"error": "Failed to decode image"}
            
            # Extract barcodes
            barcodes = self.scan_barcodes_from_image(image)
            
            if not barcodes:
                return {"error": "No barcode found in image"}
            
            # Process first barcode found
            barcode_data = barcodes[0]['data']
            
            # Look up item by barcode
            item = self.inventory_service.get_item_by_barcode(barcode_data)
            
            if not item:
                return {
                    "error": "Item not found",
                    "barcode": barcode_data,
                    "suggestions": self._get_similar_items(barcode_data)
                }
            
            # Get stock information if location provided
            stock_info = None
            if location_id:
                stock_level = self.inventory_service.get_stock_level(item.id, location_id)
                if stock_level:
                    stock_info = {
                        "current_stock": stock_level.current_stock,
                        "reserved_stock": stock_level.reserved_stock,
                        "last_updated": stock_level.last_updated.isoformat(),
                        "below_reorder_point": stock_level.current_stock <= item.reorder_point
                    }
            
            return {
                "success": True,
                "barcode": barcode_data,
                "barcode_type": barcodes[0]['type'],
                "item": {
                    "id": str(item.id),
                    "name": item.name,
                    "category": item.category,
                    "sku": item.sku,
                    "unit_of_measure": item.unit_of_measure,
                    "par_level": item.par_level,
                    "reorder_point": item.reorder_point,
                    "cost_per_unit": float(item.cost_per_unit) if item.cost_per_unit else None,
                    "selling_price": float(item.selling_price) if item.selling_price else None
                },
                "stock": stock_info,
                "all_barcodes_found": len(barcodes),
                "scan_method": barcodes[0]['method']
            }
            
        except Exception as e:
            return {"error": f"Scanning failed: {str(e)}"}
    
    def _get_similar_items(self, barcode: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar items that might match the scanned barcode"""
        # This is a simple implementation - in production you might want more sophisticated matching
        try:
            # Look for items with similar barcodes or SKUs
            items = self.db.query(InventoryItem).filter(
                InventoryItem.is_active == "true"
            ).limit(limit).all()
            
            suggestions = []
            for item in items:
                if item.barcode and (
                    barcode in item.barcode or 
                    item.barcode in barcode or
                    (item.sku and barcode in item.sku)
                ):
                    suggestions.append({
                        "id": str(item.id),
                        "name": item.name,
                        "barcode": item.barcode,
                        "sku": item.sku,
                        "category": item.category
                    })
            
            return suggestions
        except Exception:
            return []
    
    def validate_barcode_format(self, barcode: str) -> Dict[str, Any]:
        """Validate barcode format and return information about it"""
        if not barcode:
            return {"valid": False, "error": "Empty barcode"}
        
        # Basic validation for common barcode formats
        barcode = barcode.strip()
        
        # UPC-A (12 digits)
        if len(barcode) == 12 and barcode.isdigit():
            return {"valid": True, "format": "UPC-A", "length": 12}
        
        # EAN-13 (13 digits)
        elif len(barcode) == 13 and barcode.isdigit():
            return {"valid": True, "format": "EAN-13", "length": 13}
        
        # EAN-8 (8 digits)
        elif len(barcode) == 8 and barcode.isdigit():
            return {"valid": True, "format": "EAN-8", "length": 8}
        
        # Code 128 (variable length, alphanumeric)
        elif 1 <= len(barcode) <= 48:
            return {"valid": True, "format": "Code 128", "length": len(barcode)}
        
        else:
            return {"valid": False, "error": "Unknown barcode format", "length": len(barcode)}