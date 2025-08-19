from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional, Set
from uuid import UUID
import json
import asyncio
from app.services.websocket import connection_manager, inventory_ws_service
from app.core.dependencies import get_current_user_websocket
from app.schemas.user import UserResponse


router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/inventory")
async def websocket_inventory_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication"),
    location_ids: Optional[str] = Query(None, description="Comma-separated location IDs to subscribe to")
):
    """WebSocket endpoint for real-time inventory updates"""
    
    try:
        # Authenticate user
        current_user = await get_current_user_websocket(token)
        if not current_user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Parse location IDs
        location_set = set()
        if location_ids:
            try:
                location_set = {loc.strip() for loc in location_ids.split(',') if loc.strip()}
            except Exception:
                await websocket.close(code=4002, reason="Invalid location_ids format")
                return
        
        # Connect user
        await connection_manager.connect(websocket, str(current_user.id), location_set)
        
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "data": {
                "user_id": str(current_user.id),
                "subscribed_locations": list(location_set),
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        await connection_manager.send_personal_message(welcome_message, str(current_user.id))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_websocket_message(message, str(current_user.id), location_set)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # Send error message for invalid JSON
                error_message = {
                    "type": "error",
                    "data": {"message": "Invalid JSON format"}
                }
                await connection_manager.send_personal_message(error_message, str(current_user.id))
            except Exception as e:
                # Send error message for other exceptions
                error_message = {
                    "type": "error",
                    "data": {"message": f"Error processing message: {str(e)}"}
                }
                await connection_manager.send_personal_message(error_message, str(current_user.id))
                
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Connection error")
    finally:
        # Clean up connection
        if 'current_user' in locals():
            connection_manager.disconnect(str(current_user.id))


async def handle_websocket_message(message: dict, user_id: str, location_ids: Set[str]):
    """Handle incoming WebSocket messages from clients"""
    
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "ping":
        # Respond to ping with pong
        pong_message = {
            "type": "pong",
            "data": {"timestamp": asyncio.get_event_loop().time()}
        }
        await connection_manager.send_personal_message(pong_message, user_id)
        
    elif message_type == "subscribe_locations":
        # Update user's subscribed locations
        new_locations = set(data.get("location_ids", []))
        connection_manager.user_locations[user_id] = new_locations
        connection_manager.connection_metadata[user_id]["location_ids"] = new_locations
        
        response_message = {
            "type": "subscription_updated",
            "data": {
                "subscribed_locations": list(new_locations),
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        await connection_manager.send_personal_message(response_message, user_id)
        
    elif message_type == "request_sync":
        # Handle sync request
        last_sync = data.get("last_sync_timestamp")
        await inventory_ws_service.handle_sync_request(user_id, location_ids, last_sync)
        
    elif message_type == "heartbeat":
        # Update last ping time
        if user_id in connection_manager.connection_metadata:
            connection_manager.connection_metadata[user_id]["last_ping"] = asyncio.get_event_loop().time()
        
        # Send heartbeat response
        heartbeat_response = {
            "type": "heartbeat_ack",
            "data": {"timestamp": asyncio.get_event_loop().time()}
        }
        await connection_manager.send_personal_message(heartbeat_response, user_id)
        
    else:
        # Unknown message type
        error_message = {
            "type": "error",
            "data": {"message": f"Unknown message type: {message_type}"}
        }
        await connection_manager.send_personal_message(error_message, user_id)


@router.websocket("/admin")
async def websocket_admin_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication")
):
    """WebSocket endpoint for admin monitoring and management"""
    
    try:
        # Authenticate user
        current_user = await get_current_user_websocket(token)
        if not current_user or current_user.role not in ["admin", "manager"]:
            await websocket.close(code=4001, reason="Authentication failed or insufficient permissions")
            return
        
        await websocket.accept()
        
        # Send admin welcome message with connection stats
        welcome_message = {
            "type": "admin_connected",
            "data": {
                "connected_users": connection_manager.get_connected_users(),
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Keep connection alive and handle admin commands
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await handle_admin_message(message, websocket, str(current_user.id))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                error_message = {
                    "type": "error",
                    "data": {"message": f"Error processing admin message: {str(e)}"}
                }
                await websocket.send_text(json.dumps(error_message))
                
    except Exception as e:
        print(f"Admin WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Connection error")


async def handle_admin_message(message: dict, websocket: WebSocket, admin_user_id: str):
    """Handle admin WebSocket messages"""
    
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "get_connections":
        # Get current connection information
        response = {
            "type": "connection_info",
            "data": {
                "connected_users": connection_manager.get_connected_users(),
                "total_connections": len(connection_manager.active_connections),
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        await websocket.send_text(json.dumps(response))
        
    elif message_type == "broadcast_message":
        # Broadcast message to all users
        broadcast_data = data.get("message", {})
        broadcast_data["from_admin"] = admin_user_id
        broadcast_data["timestamp"] = asyncio.get_event_loop().time()
        
        await connection_manager.broadcast_to_all({
            "type": "admin_broadcast",
            "data": broadcast_data
        })
        
        # Confirm to admin
        response = {
            "type": "broadcast_sent",
            "data": {"message": "Message broadcasted to all users"}
        }
        await websocket.send_text(json.dumps(response))
        
    elif message_type == "disconnect_user":
        # Disconnect a specific user
        target_user_id = data.get("user_id")
        if target_user_id and target_user_id in connection_manager.active_connections:
            connection_manager.disconnect(target_user_id)
            
            response = {
                "type": "user_disconnected",
                "data": {"user_id": target_user_id, "message": "User disconnected by admin"}
            }
        else:
            response = {
                "type": "error",
                "data": {"message": "User not found or not connected"}
            }
        
        await websocket.send_text(json.dumps(response))
        
    else:
        # Unknown admin command
        error_message = {
            "type": "error",
            "data": {"message": f"Unknown admin command: {message_type}"}
        }
        await websocket.send_text(json.dumps(error_message))