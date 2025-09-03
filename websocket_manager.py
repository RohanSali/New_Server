import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid
from models import WebSocketMessage, ConnectionInfo, DroneCommand
from database import db_manager
from client_registry import client_registry, is_client_authorized

def serialize_datetime(obj):
    """Recursively serialize datetime, ObjectId, and other MongoDB objects in dictionaries"""
    if isinstance(obj, dict):
        return {key: serialize_datetime(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
        return str(obj)
    elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'Timestamp':
        # Handle MongoDB Timestamp objects
        return str(obj)
    elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'BSON':
        # Handle other BSON types
        return str(obj)
    else:
        return obj

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Store active connections by client type
        self.drone_connections: Dict[str, WebSocket] = {}
        self.application_connections: Dict[str, WebSocket] = {}
        
        # Store connection metadata
        self.connection_info: Dict[str, ConnectionInfo] = {}
        
        # Store drone-to-alert mapping for command routing
        self.drone_alerts: Dict[str, str] = {}  # drone_id -> alert_id
        
    async def connect(self, websocket: WebSocket, client_type: str, client_id: Optional[str] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # Check if client is authorized (if it exists in registry)
        if not is_client_authorized(client_id):
            await websocket.close(code=1008, reason="Client not authorized")
            logger.warning(f"Unauthorized connection attempt: {client_id}")
            return None
        
        # Register client in registry (auto-registration)
        client_info = client_registry.register_client(client_id, client_type)
        logger.info(f"Client registered/updated in registry: {client_id} ({client_info.name})")
        
        # Store connection based on client type
        if client_type == "drone":
            self.drone_connections[client_id] = websocket
        elif client_type == "application":
            self.application_connections[client_id] = websocket
        else:
            await websocket.close(code=1008, reason="Invalid client type")
            return None
        
        # Store connection info
        self.connection_info[client_id] = ConnectionInfo(
            client_id=client_id,
            client_type=client_type,
            connected_at=datetime.utcnow()
        )
        
        logger.info(f"New {client_type} connection: {client_id}")
        
        # Send welcome message with client info
        welcome_message = {
            "type": "connection_established",
            "client_id": client_id,
            "client_type": client_type,
            "client_name": client_info.name,
            "capabilities": client_info.capabilities,
            "total_connections": client_info.total_connections,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_personal_message(client_id, welcome_message)
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """Handle WebSocket disconnection"""
        try:
            # Update client registry status
            client_registry.unregister_client(client_id)
            
            # Remove from appropriate connection pool
            if client_id in self.drone_connections:
                del self.drone_connections[client_id]
                logger.info(f"Drone disconnected: {client_id}")
            elif client_id in self.application_connections:
                del self.application_connections[client_id]
                logger.info(f"Application disconnected: {client_id}")
            
            # Remove connection info
            if client_id in self.connection_info:
                del self.connection_info[client_id]
            
            # Remove drone-alert mapping if applicable
            if client_id in self.drone_alerts:
                del self.drone_alerts[client_id]
                
        except Exception as e:
            logger.error(f"Error during disconnect for {client_id}: {e}")
    
    async def send_personal_message(self, client_id: str, message: Dict[str, Any]):
        """Send message to a specific client"""
        try:
            websocket = None
            if client_id in self.drone_connections:
                websocket = self.drone_connections[client_id]
            elif client_id in self.application_connections:
                websocket = self.application_connections[client_id]
            
            if websocket:
                # Serialize datetime objects before sending
                serialized_message = serialize_datetime(message)
                await websocket.send_text(json.dumps(serialized_message))
            else:
                logger.warning(f"Client {client_id} not found for personal message")
                
        except Exception as e:
            logger.error(f"Error sending personal message to {client_id}: {e}")
            await self.disconnect(client_id)
    
    async def broadcast_to_applications(self, message: Dict[str, Any]):
        """Broadcast message to all connected applications"""
        if not self.application_connections:
            return
        
        disconnected_clients = []
        
        for client_id, websocket in self.application_connections.items():
            try:
                # Serialize datetime objects before sending
                serialized_message = serialize_datetime(message)
                await websocket.send_text(json.dumps(serialized_message))
            except Exception as e:
                logger.error(f"Error broadcasting to application {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def broadcast_to_drones(self, message: Dict[str, Any]):
        """Broadcast message to all connected drones"""
        if not self.drone_connections:
            return
        
        disconnected_clients = []
        
        for client_id, websocket in self.drone_connections.items():
            try:
                # Serialize datetime objects before sending
                serialized_message = serialize_datetime(message)
                await websocket.send_text(json.dumps(serialized_message))
            except Exception as e:
                logger.error(f"Error broadcasting to drone {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def send_to_drone(self, drone_id: str, message: Dict[str, Any]):
        """Send message to a specific drone"""
        if drone_id in self.drone_connections:
            await self.send_personal_message(drone_id, message)
        else:
            logger.warning(f"Drone {drone_id} not connected")
    
    async def handle_alert_from_drone(self, drone_id: str, alert_data: Dict[str, Any]):
        """Handle new alert from drone"""
        try:
            # Store the original alert data as-is with minimal required fields
            type = "alert"
            if alert_data['rl_responsed'] == 1:
                if alert_data['image_received'] == 1:
                    alert_data.update({
                        'response': 1,
                        'status': 'validated',
                    })
                else:
                    alert_data.update({
                        'response': 1,
                        'status': 'responded',
                    })
                type = "alert_responsed"
            else:
                alert_data.update({
                    'response': 0,
                    'status': 'pending',
                })
                type = "alert"
            
            # Insert alert into database
            alert_id = await db_manager.insert_alert(alert_data)
            
            # Store drone-alert mapping
            self.drone_alerts[drone_id] = alert_id
            
            # Broadcast the alert with original schema, just add alert_id once outside
            broadcast_message = {
                "type": type,
                "alert_id": str(alert_id),
                "data": serialize_datetime(alert_data.copy()),
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcast_to_applications(broadcast_message)
            
            logger.info(f"Alert {alert_id} from drone {drone_id} stored and broadcasted")
            
        except Exception as e:
            logger.error(f"Error handling alert from drone {drone_id}: {e}")
            logger.error(f"Alert data: {alert_data}")
    

    async def handle_alert_image_from_drone(self, drone_id: str, alert_image_data: Dict[str, Any]):
        """Handle alert image data from drone"""
        try:
            alert_image_id = None
            
            # Check if entry with same 'name' exists in database
            name = alert_image_data.get('name')
            if name:
                # Search for existing entry with same name
                existing_entries = await db_manager.alert_images_collection.find({'name': name}).to_list(length=None)
                
                if existing_entries:
                    # Update existing entry
                    existing_id = existing_entries[0]['_id']
                    await db_manager.alert_images_collection.update_one(
                        {'_id': existing_id},
                        {'$set': alert_image_data}
                    )
                    alert_image_id = str(existing_id)
                    logger.info(f"Updated existing alert image with name '{name}' (ID: {alert_image_id})")
                else:
                    # Create new entry
                    alert_image_id = await db_manager.create_alert_image(alert_image_data)
                    logger.info(f"Created new alert image with name '{name}' (ID: {alert_image_id})")
            else:
                # No name provided, just create new entry
                alert_image_id = await db_manager.create_alert_image(alert_image_data)
                logger.info(f"Created new alert image without name (ID: {alert_image_id})")
            
            # Broadcast to ALL clients (both applications and drones) with original schema
            broadcast_message = {
                "type": "alert_image",
                "data": serialize_datetime(alert_image_data.copy()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Broadcast to applications
            await self.broadcast_to_applications(broadcast_message)
            
            # Broadcast to all drones (except sender)
            for other_drone_id in list(self.drone_connections.keys()):
                if other_drone_id != drone_id:  # Don't send back to sender   #THINK LATER
                    await self.send_personal_message(other_drone_id, broadcast_message)
            
            logger.info(f"Alert image from drone {drone_id} processed and broadcasted to all clients")
            
        except Exception as e:
            logger.error(f"Error handling alert image from drone {drone_id}: {e}")
            logger.error(f"Alert image data: {alert_image_data}")

    async def handle_alert_image_from_application(self, app_id: str, alert_image_data: Dict[str, Any]):
        """Handle alert image data from application"""
        try:
            # Store alert image in database as-is
            alert_image_id = await db_manager.create_alert_image(alert_image_data)
            
            # Broadcast to ALL DRONES with original schema - no modifications
            broadcast_message = {
                "type": "alert_image",
                "data": serialize_datetime(alert_image_data.copy()),
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcast_to_drones(broadcast_message)
            
            logger.info(f"Alert image {alert_image_id} from application {app_id} stored and broadcasted to all drones")
            
        except Exception as e:
            logger.error(f"Error handling alert image from application {app_id}: {e}")
            logger.error(f"Alert image data: {alert_image_data}")

    
    async def handle_websocket_message(self, client_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        try:
            message_type = message_data.get('type')
            connection_info = self.connection_info.get(client_id)
            client_type = connection_info.client_type if connection_info else None
            
            if not client_type:
                logger.error(f"No client type found for {client_id}")
                return
            
            logger.info(f"Handling message from {client_id} (type: {client_type}): {message_type}")
            logger.info(f"Message data: {json.dumps(message_data, indent=2)}")
            
            if message_type == 'alert':
                if client_type == 'drone':
                    logger.info(f"Processing alert from drone {client_id}")
                    await self.handle_alert_from_drone(client_id, message_data.get('data', {}))
                else:
                    logger.warning(f"Applications cannot send alerts")
            
            elif message_type == 'alert_image':
                if client_type == 'drone':
                    await self.handle_alert_image_from_drone(client_id, message_data.get('data', {}))
                elif client_type == 'application':
                    await self.handle_alert_image_from_application(client_id, message_data.get('data', {}))
                else:
                    logger.warning(f"Invalid client type for alert_image message")
            
            elif message_type == 'ping':
                # Respond to ping
                pong_message = {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_personal_message(client_id, pong_message)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message from {client_id}: {e}")
            logger.error(f"Message data: {message_data}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics"""
        return {
            "total_connections": len(self.connection_info),
            "drone_connections": len(self.drone_connections),
            "application_connections": len(self.application_connections),
            "active_alerts": len(self.drone_alerts)
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager() 