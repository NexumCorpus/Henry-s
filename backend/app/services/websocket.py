import json
import asyncio
from typing import Dict, Set, Any, Optional
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.inventory import InventoryService
from app.models.user import User


class ConnectionManager:
    """Manages WebSocket connections for real-time inventory updates"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store user locations for targeted updates
        self.user_locations: Dict[str, Set[str]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, location_ids: Optional[Set[str]] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Store user's interested locations
        if location_ids:
            self.user_locations[user_id] = location_ids
        else:
            self.user_locations[user_id] = set()
        
        # Store connection metadata
        self.connection_metadata[user_id] = {
            "connected_at": asyncio.get_event_loop().time(),
            "last_ping": asyncio.get_event_loop().time(),
            "location_ids": location_ids or set()
        }
        
        print(f"User {user_id} connected to WebSocket")
    
    def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_locations:
            del self.user_locations[user_id]
        if user_id in self.connection_metadata:
            del self.connection_metadata[user_id]
        
        print(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                # Remove broken connection
                self.disconnect(user_id)
    
    async def broadcast_to_location(self, message: Dict[str, Any], location_id: str):
        """Broadcast a message to all users interested in a specific location"""
        disconnected_users = []
        
        for user_id, locations in self.user_locations.items():
            if location_id in locations or not locations:  # Send to all if no specific locations
                try:
                    await self.active_connections[user_id].send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error broadcasting to user {user_id}: {e}")
                    disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all connected users"""
        disconnected_users = []
        
        for user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
    
    def get_connected_users(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all connected users"""
        return {
            user_id: {
                "locations": list(self.user_locations.get(user_id, set())),
                "metadata": self.connection_metadata.get(user_id, {})
            }
            for user_id in self.active_connections
        }
    
    async def ping_all_connections(self):
        """Send ping to all connections to keep them alive"""
        ping_message = {"type": "ping", "timestamp": asyncio.get_event_loop().time()}
        await self.broadcast_to_all(ping_message)


class InventoryWebSocketService:
    """Service for handling inventory-related WebSocket communications"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def handle_inventory_update(self, item_id: UUID, location_id: UUID, 
                                    old_stock: float, new_stock: float, 
                                    user_id: str, transaction_type: str):
        """Handle inventory update and broadcast to relevant users"""
        message = {
            "type": "inventory_update",
            "data": {
                "item_id": str(item_id),
                "location_id": str(location_id),
                "old_stock": old_stock,
                "new_stock": new_stock,
                "change": new_stock - old_stock,
                "updated_by": user_id,
                "transaction_type": transaction_type,
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        
        await self.connection_manager.broadcast_to_location(message, str(location_id))
    
    async def handle_low_stock_alert(self, item_id: UUID, location_id: UUID, 
                                   current_stock: float, reorder_point: float,
                                   item_name: str):
        """Handle low stock alert and broadcast to relevant users"""
        message = {
            "type": "low_stock_alert",
            "data": {
                "item_id": str(item_id),
                "location_id": str(location_id),
                "item_name": item_name,
                "current_stock": current_stock,
                "reorder_point": reorder_point,
                "severity": "critical" if current_stock <= 0 else "warning",
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        
        await self.connection_manager.broadcast_to_location(message, str(location_id))
    
    async def handle_barcode_scan_result(self, user_id: str, scan_result: Dict[str, Any]):
        """Handle barcode scan result and send to specific user"""
        message = {
            "type": "barcode_scan_result",
            "data": scan_result
        }
        
        await self.connection_manager.send_personal_message(message, user_id)
    
    async def handle_sync_request(self, user_id: str, location_ids: Set[str], 
                                last_sync_timestamp: Optional[float] = None):
        """Handle sync request from mobile client"""
        # This would typically fetch updates since last_sync_timestamp
        # For now, we'll send current stock levels
        
        message = {
            "type": "sync_response",
            "data": {
                "sync_timestamp": asyncio.get_event_loop().time(),
                "location_ids": list(location_ids),
                "status": "complete"
            }
        }
        
        await self.connection_manager.send_personal_message(message, user_id)
    
    async def handle_offline_sync(self, user_id: str, offline_transactions: list):
        """Handle offline transaction sync from mobile client"""
        processed_transactions = []
        failed_transactions = []
        
        for transaction in offline_transactions:
            try:
                # Process each offline transaction
                # This would involve updating inventory and creating transaction records
                processed_transactions.append({
                    "local_id": transaction.get("local_id"),
                    "server_id": "generated_uuid",  # Would be actual UUID
                    "status": "processed"
                })
            except Exception as e:
                failed_transactions.append({
                    "local_id": transaction.get("local_id"),
                    "error": str(e),
                    "status": "failed"
                })
        
        message = {
            "type": "offline_sync_result",
            "data": {
                "processed": processed_transactions,
                "failed": failed_transactions,
                "sync_timestamp": asyncio.get_event_loop().time()
            }
        }
        
        await self.connection_manager.send_personal_message(message, user_id)


# Global connection manager instance
connection_manager = ConnectionManager()
inventory_ws_service = InventoryWebSocketService(connection_manager)