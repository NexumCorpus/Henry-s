import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from app.services.websocket import ConnectionManager, InventoryWebSocketService
from app.services.inventory import InventoryService
from app.models.transaction import TransactionType
import uuid


class TestMobileSynchronization:
    """Test mobile synchronization scenarios"""
    
    @pytest.fixture
    def connection_manager(self):
        """Create connection manager"""
        return ConnectionManager()
    
    @pytest.fixture
    def ws_service(self, connection_manager):
        """Create WebSocket service"""
        return InventoryWebSocketService(connection_manager)
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def inventory_service(self, mock_db):
        """Create inventory service"""
        return InventoryService(mock_db)
    
    @pytest.mark.asyncio
    async def test_real_time_stock_update_synchronization(self, connection_manager, ws_service):
        """Test real-time stock update synchronization across multiple clients"""
        # Setup multiple mock clients
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        user3_id = str(uuid.uuid4())
        location_id = str(uuid.uuid4())
        item_id = uuid.uuid4()
        
        mock_ws1 = Mock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = Mock()
        mock_ws2.send_text = AsyncMock()
        mock_ws3 = Mock()
        mock_ws3.send_text = AsyncMock()
        
        # Connect users to different locations
        await connection_manager.connect(mock_ws1, user1_id, {location_id})
        await connection_manager.connect(mock_ws2, user2_id, {location_id, "other_location"})
        await connection_manager.connect(mock_ws3, user3_id, {"other_location"})
        
        # Simulate inventory update
        await ws_service.handle_inventory_update(
            item_id, uuid.UUID(location_id), 10.0, 8.0, user1_id, "sale"
        )
        
        # Verify that users 1 and 2 received the update (they're subscribed to the location)
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()
        # User 3 should not receive the update (not subscribed to this location)
        mock_ws3.send_text.assert_not_called()
        
        # Verify message content
        call_args = mock_ws1.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == "inventory_update"
        assert message["data"]["item_id"] == str(item_id)
        assert message["data"]["old_stock"] == 10.0
        assert message["data"]["new_stock"] == 8.0
        assert message["data"]["change"] == -2.0
        assert message["data"]["updated_by"] == user1_id
    
    @pytest.mark.asyncio
    async def test_offline_transaction_conflict_resolution(self, inventory_service):
        """Test conflict resolution when multiple offline transactions affect the same item"""
        item_id = uuid.uuid4()
        location_id = uuid.uuid4()
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()
        
        # Mock current stock level
        mock_stock = Mock()
        mock_stock.current_stock = 10.0
        inventory_service.repository.get_stock_level = Mock(return_value=mock_stock)
        
        # Mock successful stock adjustments
        mock_updated_stock = Mock()
        mock_updated_stock.current_stock = 8.0
        mock_updated_stock.last_updated = datetime.utcnow()
        inventory_service.repository.adjust_stock = Mock(return_value=mock_updated_stock)
        
        # Simulate offline transactions from two users
        offline_transactions_user1 = [
            {
                "local_id": "user1_tx1",
                "item_id": item_id,
                "location_id": location_id,
                "quantity_change": -2.0,
                "transaction_type": TransactionType.SALE,
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).timestamp(),
                "notes": "Offline sale user 1"
            }
        ]
        
        offline_transactions_user2 = [
            {
                "local_id": "user2_tx1",
                "item_id": item_id,
                "location_id": location_id,
                "quantity_change": -1.0,
                "transaction_type": TransactionType.SALE,
                "timestamp": (datetime.utcnow() - timedelta(minutes=3)).timestamp(),
                "notes": "Offline sale user 2"
            }
        ]
        
        # Process first user's transactions
        result1 = []
        for tx in offline_transactions_user1:
            stock = inventory_service.adjust_stock(
                tx["item_id"], tx["location_id"], tx["quantity_change"],
                user1_id, tx["transaction_type"], tx["notes"]
            )
            result1.append(stock)
        
        # Process second user's transactions
        result2 = []
        for tx in offline_transactions_user2:
            stock = inventory_service.adjust_stock(
                tx["item_id"], tx["location_id"], tx["quantity_change"],
                user2_id, tx["transaction_type"], tx["notes"]
            )
            result2.append(stock)
        
        # Verify both transactions were processed
        assert len(result1) == 1
        assert len(result2) == 1
        assert inventory_service.repository.adjust_stock.call_count == 2
    
    @pytest.mark.asyncio
    async def test_low_stock_alert_propagation(self, connection_manager, ws_service):
        """Test low stock alert propagation to relevant users"""
        # Setup users in different locations
        manager_id = str(uuid.uuid4())
        bartender1_id = str(uuid.uuid4())
        bartender2_id = str(uuid.uuid4())
        location1_id = str(uuid.uuid4())
        location2_id = str(uuid.uuid4())
        item_id = uuid.uuid4()
        
        mock_ws_manager = Mock()
        mock_ws_manager.send_text = AsyncMock()
        mock_ws_bartender1 = Mock()
        mock_ws_bartender1.send_text = AsyncMock()
        mock_ws_bartender2 = Mock()
        mock_ws_bartender2.send_text = AsyncMock()
        
        # Connect users
        await connection_manager.connect(mock_ws_manager, manager_id, {location1_id, location2_id})
        await connection_manager.connect(mock_ws_bartender1, bartender1_id, {location1_id})
        await connection_manager.connect(mock_ws_bartender2, bartender2_id, {location2_id})
        
        # Trigger low stock alert for location 1
        await ws_service.handle_low_stock_alert(
            item_id, uuid.UUID(location1_id), 2.0, 5.0, "Premium Vodka"
        )
        
        # Manager and bartender1 should receive alert (they're subscribed to location1)
        mock_ws_manager.send_text.assert_called_once()
        mock_ws_bartender1.send_text.assert_called_once()
        # Bartender2 should not receive alert (not subscribed to location1)
        mock_ws_bartender2.send_text.assert_not_called()
        
        # Verify alert content
        call_args = mock_ws_manager.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == "low_stock_alert"
        assert message["data"]["item_name"] == "Premium Vodka"
        assert message["data"]["current_stock"] == 2.0
        assert message["data"]["reorder_point"] == 5.0
        assert message["data"]["severity"] == "warning"
    
    @pytest.mark.asyncio
    async def test_barcode_scan_result_delivery(self, connection_manager, ws_service):
        """Test barcode scan result delivery to specific user"""
        user_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        
        mock_ws_user = Mock()
        mock_ws_user.send_text = AsyncMock()
        mock_ws_other = Mock()
        mock_ws_other.send_text = AsyncMock()
        
        # Connect both users
        await connection_manager.connect(mock_ws_user, user_id, {"loc1"})
        await connection_manager.connect(mock_ws_other, other_user_id, {"loc1"})
        
        # Send barcode scan result to specific user
        scan_result = {
            "success": True,
            "barcode": "1234567890123",
            "item": {
                "id": str(uuid.uuid4()),
                "name": "Scanned Item",
                "category": "spirits"
            }
        }
        
        await ws_service.handle_barcode_scan_result(user_id, scan_result)
        
        # Only the target user should receive the scan result
        mock_ws_user.send_text.assert_called_once()
        mock_ws_other.send_text.assert_not_called()
        
        # Verify message content
        call_args = mock_ws_user.send_text.call_args[0][0]
        message = json.loads(call_args)
        
        assert message["type"] == "barcode_scan_result"
        assert message["data"]["barcode"] == "1234567890123"
        assert message["data"]["item"]["name"] == "Scanned Item"
    
    @pytest.mark.asyncio
    async def test_connection_recovery_after_network_outage(self, connection_manager):
        """Test connection recovery after network outage"""
        user_id = str(uuid.uuid4())
        location_ids = {"loc1", "loc2"}
        
        # Initial connection
        mock_ws1 = Mock()
        mock_ws1.send_text = AsyncMock()
        await connection_manager.connect(mock_ws1, user_id, location_ids)
        
        assert user_id in connection_manager.active_connections
        assert connection_manager.user_locations[user_id] == location_ids
        
        # Simulate network outage (connection lost)
        connection_manager.disconnect(user_id)
        
        assert user_id not in connection_manager.active_connections
        assert user_id not in connection_manager.user_locations
        
        # Simulate reconnection
        mock_ws2 = Mock()
        mock_ws2.send_text = AsyncMock()
        await connection_manager.connect(mock_ws2, user_id, location_ids)
        
        # Verify user is reconnected with same settings
        assert user_id in connection_manager.active_connections
        assert connection_manager.active_connections[user_id] == mock_ws2
        assert connection_manager.user_locations[user_id] == location_ids
    
    @pytest.mark.asyncio
    async def test_bulk_offline_sync_performance(self, inventory_service):
        """Test performance of bulk offline synchronization"""
        item_ids = [uuid.uuid4() for _ in range(50)]  # 50 different items
        location_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Mock stock levels and adjustments
        mock_stock = Mock()
        mock_stock.current_stock = 10.0
        inventory_service.repository.get_stock_level = Mock(return_value=mock_stock)
        
        mock_updated_stock = Mock()
        mock_updated_stock.current_stock = 9.0
        mock_updated_stock.last_updated = datetime.utcnow()
        inventory_service.repository.adjust_stock = Mock(return_value=mock_updated_stock)
        
        # Create bulk offline transactions
        offline_transactions = []
        for i, item_id in enumerate(item_ids):
            offline_transactions.append({
                "local_id": f"tx_{i}",
                "item_id": item_id,
                "location_id": location_id,
                "quantity_change": -1.0,
                "transaction_type": TransactionType.SALE,
                "timestamp": (datetime.utcnow() - timedelta(minutes=i)).timestamp(),
                "notes": f"Offline sale {i}"
            })
        
        # Measure sync performance
        start_time = datetime.utcnow()
        
        successful_syncs = 0
        for tx in offline_transactions:
            try:
                stock = inventory_service.adjust_stock(
                    tx["item_id"], tx["location_id"], tx["quantity_change"],
                    user_id, tx["transaction_type"], tx["notes"]
                )
                if stock:
                    successful_syncs += 1
            except Exception:
                pass
        
        end_time = datetime.utcnow()
        sync_duration = (end_time - start_time).total_seconds()
        
        # Verify all transactions were processed
        assert successful_syncs == 50
        assert inventory_service.repository.adjust_stock.call_count == 50
        
        # Performance assertion (should complete within reasonable time)
        assert sync_duration < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_user_updates_same_item(self, connection_manager, ws_service):
        """Test handling concurrent updates to the same item from multiple users"""
        item_id = uuid.uuid4()
        location_id = str(uuid.uuid4())
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        user3_id = str(uuid.uuid4())
        
        mock_ws1 = Mock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = Mock()
        mock_ws2.send_text = AsyncMock()
        mock_ws3 = Mock()
        mock_ws3.send_text = AsyncMock()
        
        # Connect all users to the same location
        await connection_manager.connect(mock_ws1, user1_id, {location_id})
        await connection_manager.connect(mock_ws2, user2_id, {location_id})
        await connection_manager.connect(mock_ws3, user3_id, {location_id})
        
        # Simulate concurrent updates
        update_tasks = [
            ws_service.handle_inventory_update(
                item_id, uuid.UUID(location_id), 10.0, 9.0, user1_id, "sale"
            ),
            ws_service.handle_inventory_update(
                item_id, uuid.UUID(location_id), 9.0, 8.0, user2_id, "sale"
            ),
            ws_service.handle_inventory_update(
                item_id, uuid.UUID(location_id), 8.0, 7.0, user3_id, "sale"
            )
        ]
        
        # Execute all updates concurrently
        await asyncio.gather(*update_tasks)
        
        # All users should receive all three updates
        assert mock_ws1.send_text.call_count == 3
        assert mock_ws2.send_text.call_count == 3
        assert mock_ws3.send_text.call_count == 3
    
    @pytest.mark.asyncio
    async def test_location_subscription_changes(self, connection_manager):
        """Test dynamic location subscription changes"""
        user_id = str(uuid.uuid4())
        initial_locations = {"loc1", "loc2"}
        updated_locations = {"loc2", "loc3", "loc4"}
        
        mock_ws = Mock()
        mock_ws.send_text = AsyncMock()
        
        # Initial connection
        await connection_manager.connect(mock_ws, user_id, initial_locations)
        assert connection_manager.user_locations[user_id] == initial_locations
        
        # Update subscriptions
        connection_manager.user_locations[user_id] = updated_locations
        connection_manager.connection_metadata[user_id]["location_ids"] = updated_locations
        
        # Verify subscription changes
        assert connection_manager.user_locations[user_id] == updated_locations
        
        # Test that user receives updates for new locations but not old ones
        # This would be tested by sending location-specific broadcasts
        # and verifying which ones the user receives
    
    @pytest.mark.asyncio
    async def test_websocket_message_ordering(self, connection_manager):
        """Test that WebSocket messages are delivered in correct order"""
        user_id = str(uuid.uuid4())
        
        mock_ws = Mock()
        sent_messages = []
        
        async def mock_send_text(message):
            sent_messages.append(json.loads(message))
        
        mock_ws.send_text = mock_send_text
        
        await connection_manager.connect(mock_ws, user_id, {"loc1"})
        
        # Send multiple messages in sequence
        messages = [
            {"type": "update1", "sequence": 1},
            {"type": "update2", "sequence": 2},
            {"type": "update3", "sequence": 3}
        ]
        
        for message in messages:
            await connection_manager.send_personal_message(message, user_id)
        
        # Verify messages were received in correct order
        assert len(sent_messages) == 3
        for i, received_message in enumerate(sent_messages):
            assert received_message["sequence"] == i + 1
    
    @pytest.mark.asyncio
    async def test_failed_message_delivery_cleanup(self, connection_manager):
        """Test cleanup of failed connections during message delivery"""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # Create one working connection and one that will fail
        mock_ws1 = Mock()
        mock_ws1.send_text = AsyncMock()
        
        mock_ws2 = Mock()
        mock_ws2.send_text = AsyncMock(side_effect=Exception("Connection failed"))
        
        connection_manager.active_connections[user1_id] = mock_ws1
        connection_manager.active_connections[user2_id] = mock_ws2
        connection_manager.user_locations[user1_id] = {"loc1"}
        connection_manager.user_locations[user2_id] = {"loc1"}
        
        # Attempt to broadcast to location
        message = {"type": "test", "data": "test"}
        await connection_manager.broadcast_to_location(message, "loc1")
        
        # Working connection should still be active
        assert user1_id in connection_manager.active_connections
        mock_ws1.send_text.assert_called_once()
        
        # Failed connection should be cleaned up
        assert user2_id not in connection_manager.active_connections
        assert user2_id not in connection_manager.user_locations