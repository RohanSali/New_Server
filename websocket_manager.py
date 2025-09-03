import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid
from models import WebSocketMessage, ConnectionInfo, DroneCommand
from database import db_manager

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
        
        # Send welcome message
        welcome_message = {
            "type": "connection_established",
            "client_id": client_id,
            "client_type": client_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_personal_message(client_id, welcome_message)
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """Handle WebSocket disconnection"""
        try:
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
    
    async def send_to_drone(self, drone_id: str, message: Dict[str, Any]):
        """Send message to a specific drone"""
        if drone_id in self.drone_connections:
            await self.send_personal_message(drone_id, message)
        else:
            logger.warning(f"Drone {drone_id} not connected")
    
    async def handle_alert_from_drone(self, drone_id: str, alert_data: Dict[str, Any]):
        """Handle new alert from drone"""
        try:
            # Set initial values
            alert_data.update({
                'response': 0,
                'image_received': 0,
                'status': 'pending'
            })
            
            # Insert alert into database
            alert_id = await db_manager.insert_alert(alert_data)
            
            # Store drone-alert mapping
            self.drone_alerts[drone_id] = alert_id
            
            # Create a properly serialized alert for broadcasting
            # Use the original alert data but ensure it's properly serialized
            broadcast_alert = serialize_datetime(alert_data.copy())
            
            # Add the alert_id to the broadcast data
            broadcast_alert['id'] = str(alert_id)
            
            # Broadcast to all applications
            broadcast_message = {
                "type": "new_alert",
                "alert": broadcast_alert,
                "alert_id": str(alert_id),  # Convert ObjectId to string
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcast_to_applications(broadcast_message)
            
            logger.info(f"Alert {alert_id} from drone {drone_id} processed and broadcasted")
            logger.info(f"Broadcast message: {json.dumps(broadcast_message, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error handling alert from drone {drone_id}: {e}")
            logger.error(f"Alert data: {alert_data}")
    
    async def handle_response_from_application(self, alert_id: str, response_data: Dict[str, Any]):
        """Handle response from application (RL model output)"""
        try:
            # Update alert in database
            update_data = {
                'response': 1,
                'actions': response_data.get('actions', []),
                'status': 'responded'
            }
            
            success = await db_manager.update_alert(alert_id, update_data)
            
            if success:
                # Find the drone that sent this alert
                drone_id = None
                for d_id, a_id in self.drone_alerts.items():
                    if a_id == alert_id:
                        drone_id = d_id
                        break
                
                if drone_id:
                    # Send command to drone
                    command_message = {
                        "type": "drone_command",
                        "alert_id": alert_id,
                        "actions": response_data.get('actions', []),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.send_to_drone(drone_id, command_message)
                    
                    logger.info(f"Command sent to drone {drone_id} for alert {alert_id}")
                else:
                    logger.warning(f"No drone found for alert {alert_id}")
            
        except Exception as e:
            logger.error(f"Error handling response from application for alert {alert_id}: {e}")
    
    async def handle_image_from_drone(self, drone_id: str, image_data: Dict[str, Any]):
        """Handle image data from drone"""
        try:
            alert_id = image_data.get('alert_id')
            image_url = image_data.get('image_url')
            
            if alert_id and image_url:
                # Update alert in database
                update_data = {
                    'image_received': 1,
                    'image_url': image_url,
                    'status': 'completed'
                }
                
                success = await db_manager.update_alert(alert_id, update_data)
                
                if success:
                    # Broadcast to applications
                    broadcast_message = {
                        "type": "image_received",
                        "alert_id": alert_id,
                        "image_url": image_url,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.broadcast_to_applications(broadcast_message)
                    
                    logger.info(f"Image received for alert {alert_id} from drone {drone_id}")
            
        except Exception as e:
            logger.error(f"Error handling image from drone {drone_id}: {e}")

    async def handle_alert_image_from_drone(self, drone_id: str, alert_image_data: Dict[str, Any]):
        """Handle alert image data from drone"""
        try:
            # Create alert image in database
            alert_image_id = await db_manager.create_alert_image(alert_image_data)
            
            # Broadcast to applications
            broadcast_message = {
                "type": "alert_image_received",
                "alert_image_id": alert_image_id,
                "alert_image": serialize_datetime(alert_image_data),
                "drone_id": drone_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcast_to_applications(broadcast_message)
            
            logger.info(f"Alert image {alert_image_id} from drone {drone_id} processed and broadcasted")
            
        except Exception as e:
            logger.error(f"Error handling alert image from drone {drone_id}: {e}")
            logger.error(f"Alert image data: {alert_image_data}")

    async def handle_alert_image_from_application(self, app_id: str, alert_image_data: Dict[str, Any]):
        """Handle alert image data from application"""
        try:
            # Create alert image in database
            alert_image_id = await db_manager.create_alert_image(alert_image_data)
            
            # Broadcast to other applications
            broadcast_message = {
                "type": "alert_image_received",
                "alert_image_id": alert_image_id,
                "alert_image": serialize_datetime(alert_image_data),
                "app_id": app_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcast_to_applications(broadcast_message)
            
            # Forward to drones if specified
            drone_id = alert_image_data.get('drone_id')
            if drone_id and drone_id != "No Drone":
                drone_message = {
                    "type": "alert_image",
                    "alert_image_id": alert_image_id,
                    "alert_image": serialize_datetime(alert_image_data),
                    "app_id": app_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_to_drone(drone_id, drone_message)
                logger.info(f"Alert image {alert_image_id} forwarded to drone {drone_id}")
            
            logger.info(f"Alert image {alert_image_id} from application {app_id} processed and broadcasted")
            
        except Exception as e:
            logger.error(f"Error handling alert image from application {app_id}: {e}")
            logger.error(f"Alert image data: {alert_image_data}")

    async def handle_processing_task_from_application(self, app_id: str, task_data: Dict[str, Any]):
        """Handle processing task from application"""
        try:
            # Create processing task in database
            task_id = await db_manager.create_processing_task(task_data)
            
            # Find the target drone
            drone_id = task_data.get('drone_id')
            if drone_id and drone_id in self.drone_connections:
                # Send task to drone
                task_message = {
                    "type": "processing_task",
                    "task_id": task_id,
                    "task_data": serialize_datetime(task_data),
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.send_to_drone(drone_id, task_message)
                
                logger.info(f"Processing task {task_id} sent to drone {drone_id}")
            else:
                logger.warning(f"Drone {drone_id} not connected or not found")
            
        except Exception as e:
            logger.error(f"Error handling processing task from application {app_id}: {e}")
            logger.error(f"Task data: {task_data}")

    async def handle_processing_result_from_drone(self, drone_id: str, result_data: Dict[str, Any]):
        """Handle processing result from drone"""
        try:
            task_id = result_data.get('task_id')
            
            # Create processing result in database
            result_id = await db_manager.create_processing_result(result_data)
            
            # Update task status to completed
            await db_manager.update_task_status(task_id, 'completed')
            
            # Find the application that created the task
            task = await db_manager.get_processing_task(task_id)
            app_id = task.get('app_id') if task else None
            
            # Broadcast result to applications
            broadcast_message = {
                "type": "processing_result_received",
                "result_id": result_id,
                "task_id": task_id,
                "result_data": serialize_datetime(result_data),
                "drone_id": drone_id,
                "app_id": app_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.broadcast_to_applications(broadcast_message)
            
            logger.info(f"Processing result {result_id} for task {task_id} from drone {drone_id} processed and broadcasted")
            
        except Exception as e:
            logger.error(f"Error handling processing result from drone {drone_id}: {e}")
            logger.error(f"Result data: {result_data}")

    async def handle_task_status_update_from_drone(self, drone_id: str, status_data: Dict[str, Any]):
        """Handle task status update from drone"""
        try:
            task_id = status_data.get('task_id')
            status = status_data.get('status')
            additional_data = status_data.get('additional_data', {})
            
            # Update task status in database
            success = await db_manager.update_task_status(task_id, status, additional_data)
            
            if success:
                # Broadcast status update to applications
                broadcast_message = {
                    "type": "task_status_update",
                    "task_id": task_id,
                    "status": status,
                    "drone_id": drone_id,
                    "additional_data": additional_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.broadcast_to_applications(broadcast_message)
                
                logger.info(f"Task {task_id} status updated to {status} by drone {drone_id}")
            
        except Exception as e:
            logger.error(f"Error handling task status update from drone {drone_id}: {e}")
            logger.error(f"Status data: {status_data}")
    
    async def handle_websocket_message(self, client_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        try:
            message_type = message_data.get('type')
            client_type = self.connection_info.get(client_id, {}).client_type
            
            logger.info(f"Handling message from {client_id} (type: {client_type}): {message_type}")
            logger.info(f"Message data: {json.dumps(message_data, indent=2)}")
            
            if message_type == 'alert':
                if client_type == 'drone':
                    logger.info(f"Processing alert from drone {client_id}")
                    await self.handle_alert_from_drone(client_id, message_data.get('data', {}))
                else:
                    logger.warning(f"Applications cannot send alerts")
            
            elif message_type == 'response':
                if client_type == 'application':
                    alert_id = message_data.get('alert_id')
                    if alert_id:
                        await self.handle_response_from_application(alert_id, message_data.get('data', {}))
                else:
                    logger.warning(f"Drones cannot send responses")
            
            elif message_type == 'image':
                if client_type == 'drone':
                    await self.handle_image_from_drone(client_id, message_data.get('data', {}))
                else:
                    logger.warning(f"Applications cannot send images")
            
            elif message_type == 'alert_image':
                if client_type == 'drone':
                    await self.handle_alert_image_from_drone(client_id, message_data.get('data', {}))
                elif client_type == 'application':
                    await self.handle_alert_image_from_application(client_id, message_data.get('data', {}))
                else:
                    logger.warning(f"Invalid client type for alert_image message")
            
            elif message_type == 'processing_task':
                if client_type == 'application':
                    await self.handle_processing_task_from_application(client_id, message_data.get('data', {}))
                else:
                    logger.warning(f"Drones cannot send processing tasks")
            
            elif message_type == 'processing_result':
                if client_type == 'drone':
                    await self.handle_processing_result_from_drone(client_id, message_data.get('data', {}))
                else:
                    logger.warning(f"Applications cannot send processing results")
            
            elif message_type == 'task_status_update':
                if client_type == 'drone':
                    await self.handle_task_status_update_from_drone(client_id, message_data.get('data', {}))
                else:
                    logger.warning(f"Applications cannot send task status updates")
            
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