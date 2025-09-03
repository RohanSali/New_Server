#!/usr/bin/env python3
"""
Example Application Client
Simulates an application that receives alerts and sends responses via WebSocket
"""

import asyncio
import websockets
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List

class ApplicationClient:
    def __init__(self, app_id: str, server_url: str = "wss://droneserver-5pfg.onrender.com"):
        self.app_id = app_id
        self.server_url = f"{server_url}/ws/application/{app_id}"
        self.websocket = None
        self.connected = False
        self.pending_alerts = {}  # Store alerts waiting for response
        
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            print(f"Application {self.app_id} connected to server")
            
            # Send initial connection message
            await self.send_message({
                "type": "ping",
                "data": {"app_id": self.app_id}
            })
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False
    
    async def disconnect(self):
        """Disconnect from the server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print(f"Application {self.app_id} disconnected")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the server"""
        if not self.connected or not self.websocket:
            print("Not connected to server")
            return
        
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending message: {e}")
            self.connected = False
    
    async def send_response(self, alert_id: str, actions: List[str]):
        """Send a response to an alert"""
        response_data = {
            "type": "response",
            "alert_id": alert_id,
            "data": {
                "actions": actions,
                "response": 1,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await self.send_message(response_data)
        print(f"Response sent for alert {alert_id}: {actions}")
    
    def simulate_rl_model_processing(self, alert_data: Dict[str, Any]) -> List[str]:
        """Simulate RL model processing to determine actions"""
        alert_type = alert_data.get("alert_type", "")
        score = alert_data.get("score", 0.0)
        
        # Simple rule-based action selection (simulating RL model)
        actions = []
        
        if alert_type == "intrusion":
            if score > 0.8:
                actions = ["activate_security_system", "notify_authorities", "record_video"]
            else:
                actions = ["monitor_closely", "record_video"]
        
        elif alert_type == "fire":
            if score > 0.7:
                actions = ["activate_fire_suppression", "notify_fire_department", "evacuate_area"]
            else:
                actions = ["monitor_closely", "notify_security"]
        
        elif alert_type == "accident":
            actions = ["notify_emergency_services", "record_evidence", "secure_area"]
        
        elif alert_type == "security_breach":
            actions = ["lockdown_area", "notify_security", "track_intruder"]
        
        elif alert_type == "environmental":
            actions = ["monitor_conditions", "adjust_environmental_controls"]
        
        else:
            actions = ["investigate", "monitor_closely"]
        
        return actions
    
    async def handle_new_alert(self, alert_data: Dict[str, Any]):
        """Handle a new alert received from the server"""
        alert_id = alert_data.get("alert_id")
        alert_type = alert_data.get("alert_type")
        score = alert_data.get("score", 0.0)
        location = alert_data.get("location", {})
        
        print(f"\n=== NEW ALERT RECEIVED ===")
        print(f"Alert ID: {alert_id}")
        print(f"Type: {alert_type}")
        print(f"Score: {score:.2f}")
        print(f"Location: {location}")
        print(f"Description: {alert_data.get('description', 'N/A')}")
        print("=" * 30)
        
        # Store alert for processing
        self.pending_alerts[alert_id] = alert_data
        
        # Simulate RL model processing time
        print("Processing with RL model...")
        await asyncio.sleep(3)  # Simulate processing time
        
        # Generate actions using simulated RL model
        actions = self.simulate_rl_model_processing(alert_data)
        
        print(f"RL Model determined actions: {actions}")
        
        # Send response back to server
        await self.send_response(alert_id, actions)
        
        # Remove from pending alerts
        if alert_id in self.pending_alerts:
            del self.pending_alerts[alert_id]
    
    async def handle_alert_update(self, change_event: Dict[str, Any]):
        """Handle alert updates from the change stream"""
        operation_type = change_event.get("operation_type")
        alert = change_event.get("alert", {})
        alert_id = alert.get("alert_id")
        
        print(f"\n=== ALERT UPDATE ===")
        print(f"Operation: {operation_type}")
        print(f"Alert ID: {alert_id}")
        
        if operation_type == "update":
            if alert.get("image_received") == 1:
                print(f"Image received for alert {alert_id}")
                print(f"Image URL: {alert.get('image_url')}")
            elif alert.get("response") == 1:
                print(f"Response processed for alert {alert_id}")
                print(f"Actions: {alert.get('actions')}")
        
        print("=" * 20)
    
    async def handle_image_received(self, image_data: Dict[str, Any]):
        """Handle image received notification"""
        alert_id = image_data.get("alert_id")
        image_url = image_data.get("image_url")
        
        print(f"\n=== IMAGE RECEIVED ===")
        print(f"Alert ID: {alert_id}")
        print(f"Image URL: {image_url}")
        print("=" * 20)
    
    async def listen_for_messages(self):
        """Listen for incoming messages from the server"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "connection_established":
                        print(f"Connection established: {data}")
                    
                    elif message_type == "initial_alerts":
                        alerts = data.get("alerts", [])
                        print(f"Received {len(alerts)} initial alerts")
                        for alert in alerts:
                            print(f"  - {alert.get('alert_id')}: {alert.get('alert_type')}")
                    
                    elif message_type == "new_alert":
                        alert_data = data.get("alert", {})
                        await self.handle_new_alert(alert_data)
                    
                    elif message_type == "alert_update":
                        change_event = data.get("change", {})
                        await self.handle_alert_update(change_event)
                    
                    elif message_type == "image_received":
                        image_data = data.get("data", {})
                        await self.handle_image_received(image_data)
                    
                    elif message_type == "pong":
                        print("Received pong from server")
                    
                    else:
                        print(f"Received message: {data}")
                        
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed by server")
            self.connected = False
        except Exception as e:
            print(f"Error receiving message: {e}")
            self.connected = False
    
    async def run(self):
        """Main run loop for the application client"""
        await self.connect()
        
        if not self.connected:
            return
        
        # Start listening for messages in background
        listen_task = asyncio.create_task(self.listen_for_messages())
        
        try:
            # Keep the application running
            while self.connected:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("Shutting down application client...")
        finally:
            listen_task.cancel()
            await self.disconnect()

async def main():
    """Main function to run the application client"""
    app_id = input("Enter application ID (or press Enter for auto-generated): ").strip()
    if not app_id:
        app_id = f"app_{uuid.uuid4().hex[:8]}"
    
    app = ApplicationClient(app_id)
    await app.run()

if __name__ == "__main__":
    asyncio.run(main()) 