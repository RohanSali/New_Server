#!/usr/bin/env python3
"""
Example Drone Client
Simulates a drone that sends alerts and receives commands via WebSocket
"""

import asyncio
import websockets
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any

class DroneClient:
    def __init__(self, drone_id: str, server_url: str = None):
        self.drone_id = drone_id
        
        # Try different server URLs if the default fails
        if server_url is None:
            # Try common Railway.app patterns
            possible_urls = [
                "wss://droneserver-5pfg.onrender.com",
                "wss://droneserver-5pfg.onrender.com",  # Replace with your actual app name
                "wss://localhost:8000",  # For local development
                "ws://localhost:8000"    # For local development without SSL
            ]
            self.server_url = possible_urls[0]  # Start with the first one
            self.fallback_urls = possible_urls[1:]
        else:
            self.server_url = server_url
            self.fallback_urls = []
            
        self.websocket = None
        self.connected = False
        
    async def connect(self):
        """Connect to the WebSocket server with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Construct the full WebSocket URL
                full_url = f"{self.server_url}/ws/drone/{self.drone_id}"
                print(f"🔗 Attempt {attempt + 1}/{max_retries}: Connecting to {full_url}")
                
                # Add timeout to connection
                self.websocket = await asyncio.wait_for(
                    websockets.connect(full_url),
                    timeout=10.0
                )
                self.connected = True
                print(f"✅ Drone {self.drone_id} connected to server successfully!")
                
                # Send initial connection message
                await self.send_message({
                    "type": "ping",
                    "data": {"drone_id": self.drone_id}
                })
                print("📤 Sent initial ping message")
                return  # Success, exit retry loop
                
            except asyncio.TimeoutError:
                print(f"⏰ Connection timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    
            except Exception as e:
                print(f"❌ Connection failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("💥 All connection attempts failed")
                    self.connected = False
    
    async def disconnect(self):
        """Disconnect from the server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print(f"Drone {self.drone_id} disconnected")
    
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
    
    async def send_alert(self, alert_type: str, score: float, location: Dict[str, float], description: str = None):
        """Send an alert to the server"""
        if not self.connected:
            print("❌ Cannot send alert: Not connected to server")
            return False
            
        alert_data = {
            "type": "alert",
            "data": {
                "alert_type": alert_type,
                "score": score,
                "location": location,
                "drone_id": self.drone_id,
                "description": description,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        try:
            await self.send_message(alert_data)
            print(f"✅ Alert sent successfully: {alert_type} at {location}")
            return True
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")
            return False
    
    async def send_image(self, alert_id: str, image_url: str):
        """Send image data to the server"""
        image_data = {
            "type": "image",
            "data": {
                "alert_id": alert_id,
                "image_url": image_url,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await self.send_message(image_data)
        print(f"Image sent for alert {alert_id}")
    
    async def handle_command(self, command_data: Dict[str, Any]):
        """Handle commands received from the server"""
        command_type = command_data.get("type")
        alert_id = command_data.get("alert_id")
        actions = command_data.get("actions", [])
        
        print(f"Received command: {command_type}")
        print(f"Alert ID: {alert_id}")
        print(f"Actions: {actions}")
        
        # Simulate executing the command
        print("Executing drone actions...")
        await asyncio.sleep(2)  # Simulate processing time
        
        # Simulate sending back an image
        image_url = f"https://web-production-190fc.up.railway.app/uploads/drone_{self.drone_id}_alert_{alert_id}.jpg"
        await self.send_image(alert_id, image_url)
    
    async def handle_alert_image(self, alert_image_data: Dict[str, Any]):
        """Handle alert image received from application via server"""
        alert_image_id = alert_image_data.get("alert_image_id")
        alert_image = alert_image_data.get("alert_image", {})
        app_id = alert_image_data.get("app_id")
        
        print(f"\n=== ALERT IMAGE RECEIVED ===")
        print(f"Alert Image ID: {alert_image_id}")
        print(f"From Application: {app_id}")
        print(f"Object Name: {alert_image.get('name', 'N/A')}")
        print(f"Location: {alert_image.get('location', 'N/A')}")
        print(f"Detection Status: {'Found' if alert_image.get('found', 0) == 1 else 'Not Found'}")
        print(f"Timestamp: {alert_image.get('timestamp', 'N/A')}")
        
        # The actual_image and matched_frame are base64 encoded
        actual_image_blob = alert_image.get('actual_image')
        matched_frame_blob = alert_image.get('matched_frame')
        
        if actual_image_blob:
            print(f"✅ Received actual image (base64 encoded, {len(actual_image_blob)} chars)")
        if matched_frame_blob:
            print(f"✅ Received matched frame (base64 encoded, {len(matched_frame_blob)} chars)")
        
        # Decode and save the images
        try:
            import base64
            import os
            
            # Create uploads directory if it doesn't exist
            uploads_dir = "uploads"
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Decode and save actual image
            if actual_image_blob:
                actual_image_bytes = base64.b64decode(actual_image_blob)
                actual_image_path = f"{uploads_dir}/drone_{self.drone_id}_alert_{alert_image_id}_actual.jpg"
                with open(actual_image_path, "wb") as f:
                    f.write(actual_image_bytes)
                print(f"💾 Saved actual image to: {actual_image_path}")
            
            # Decode and save matched frame
            if matched_frame_blob:
                matched_frame_bytes = base64.b64decode(matched_frame_blob)
                matched_frame_path = f"{uploads_dir}/drone_{self.drone_id}_alert_{alert_image_id}_matched.jpg"
                with open(matched_frame_path, "wb") as f:
                    f.write(matched_frame_bytes)
                print(f"💾 Saved matched frame to: {matched_frame_path}")
            
            print("✅ Successfully processed and saved alert images")
            
        except Exception as e:
            print(f"❌ Error processing images: {e}")
        
        print("=" * 30)
    
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
                    
                    elif message_type == "drone_command":
                        await self.handle_command(data)
                    
                    elif message_type == "alert_image":
                        await self.handle_alert_image(data)
                    
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
        """Main run loop for the drone client"""
        print("🚁 Starting drone client...")
        
        # Connect to server
        await self.connect()
        
        if not self.connected:
            print("💥 Failed to connect to server. Exiting.")
            return
        
        print("🎯 Drone client is running and connected!")
        print("📡 Listening for messages from server...")
        print("📤 Sending periodic alerts every 30 seconds...")
        print("🛑 Press Ctrl+C to stop the drone client")
        print("=" * 50)
        
        # Start listening for messages in background
        listen_task = asyncio.create_task(self.listen_for_messages())
        
        try:
            # Simulate periodic alerts
            alert_count = 0
            while self.connected:
                # Send a random alert every 30 seconds
                if alert_count % 6 == 0:  # Every 30 seconds (6 * 5 second sleep)
                    alert_types = ["intrusion", "fire", "accident", "security_breach", "environmental"]
                    alert_type = alert_types[alert_count % len(alert_types)]
                    
                    location = {
                        "lat": 40.7128 + (alert_count * 0.001),  # Simulate movement
                        "lng": -74.0060 + (alert_count * 0.001)
                    }
                    
                    score = 0.7 + (alert_count * 0.1) % 0.3  # Random score between 0.7-1.0
                    
                    success = await self.send_alert(
                        alert_type=alert_type,
                        score=score,
                        location=location,
                        description=f"Simulated {alert_type} alert #{alert_count + 1}"
                    )
                    
                    if not success:
                        print("⚠️ Alert sending failed, but continuing...")
                
                await asyncio.sleep(5)  # Wait 5 seconds
                alert_count += 1
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down drone client...")
        except Exception as e:
            print(f"❌ Unexpected error in drone client: {e}")
        finally:
            print("🔄 Cleaning up...")
            listen_task.cancel()
            await self.disconnect()
            print("✅ Drone client stopped successfully")

async def main():
    """Main function to run the drone client"""
    print("🚁 Drone Client Setup")
    print("=" * 40)
    
    drone_id = input("Enter drone ID (or press Enter for auto-generated): ").strip()
    if not drone_id:
        drone_id = f"drone_{uuid.uuid4().hex[:8]}"
    
    print(f"\n🔧 Server Configuration:")
    print("1. Use Railway server (web-production-190fc.up.railway.app)")
    print("2. Use local server (localhost:8000)")
    print("3. Enter custom server URL")
    
    choice = input("\nEnter choice (1-3) or press Enter for default: ").strip()
    
    server_url = None
    if choice == "2":
        server_url = "ws://localhost:8000"
    elif choice == "3":
        server_url = input("Enter server URL (e.g., wss://your-server.com): ").strip()
        if not server_url.startswith(("ws://", "wss://")):
            server_url = f"wss://{server_url}"
    else:
        # Default to Railway server
        server_url = "wss://web-production-190fc.up.railway.app"
    
    print(f"\n🚁 Starting drone with ID: {drone_id}")
    print(f"🌐 Using server: {server_url}")
    
    drone = DroneClient(drone_id, server_url)
    await drone.run()

if __name__ == "__main__":
    asyncio.run(main()) 