#!/usr/bin/env python3
"""
Test script to verify updated message handling logic
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

# Test message templates
ALERT_MESSAGE = {
    "type": "alert",
    "data": {
        "alert": "Person Detected",
        "drone_id": "test_drone_001",
        "alert_location": [40.7128, -74.0060, 100],
        "score": 0.85,
        "timestamp": datetime.utcnow().isoformat(),
        "description": "Suspicious person detected in restricted area"
    }
}

ALERT_IMAGE_FROM_APP = {
    "type": "alert_image",
    "data": {
        "found": 1,
        "name": "test_person_001",
        "drone_id": "test_drone_001",
        "actual_image": "base64_encoded_image_data_here",
        "matched_frame": "base64_encoded_frame_data_here",
        "location": [40.7128, -74.0060, 100],
        "timestamp": datetime.utcnow().isoformat()
    }
}

ALERT_IMAGE_FROM_DRONE = {
    "type": "alert_image", 
    "data": {
        "found": 1,
        "name": "test_person_001",  # This will trigger name-based matching
        "drone_id": "test_drone_002",
        "actual_image": "updated_base64_encoded_image_data",
        "matched_frame": "updated_base64_encoded_frame_data",
        "location": [40.7589, -73.9851, 150],
        "timestamp": datetime.utcnow().isoformat(),
        "confidence": 0.92,
        "additional_data": "This should update existing entry"
    }
}

async def test_drone_client(drone_id: str, message_to_send: dict, server_url: str = "ws://localhost:8000"):
    """Test drone client"""
    try:
        uri = f"{server_url}/ws/drone/{drone_id}"
        print(f"🚁 Connecting drone {drone_id} to {uri}")
        
        async with websockets.connect(uri) as websocket:
            print(f"✅ Drone {drone_id} connected")
            
            # Listen for incoming messages in background
            listen_task = asyncio.create_task(listen_for_messages(websocket, drone_id))
            
            # Send test message
            print(f"📤 Sending {message_to_send['type']} message from drone {drone_id}")
            await websocket.send(json.dumps(message_to_send))
            
            # Wait a bit for responses
            await asyncio.sleep(2)
            
            listen_task.cancel()
            
    except Exception as e:
        print(f"❌ Error in drone {drone_id}: {e}")

async def test_app_client(app_id: str, message_to_send: dict, server_url: str = "ws://localhost:8000"):
    """Test application client"""
    try:
        uri = f"{server_url}/ws/application/{app_id}"
        print(f"📱 Connecting application {app_id} to {uri}")
        
        async with websockets.connect(uri) as websocket:
            print(f"✅ Application {app_id} connected")
            
            # Listen for incoming messages in background
            listen_task = asyncio.create_task(listen_for_messages(websocket, app_id))
            
            # Send test message
            print(f"📤 Sending {message_to_send['type']} message from application {app_id}")
            await websocket.send(json.dumps(message_to_send))
            
            # Wait a bit for responses
            await asyncio.sleep(2)
            
            listen_task.cancel()
            
    except Exception as e:
        print(f"❌ Error in application {app_id}: {e}")

async def listen_for_messages(websocket, client_id):
    """Listen for messages from server"""
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"📥 {client_id} received: {data['type']}")
            print(f"   Data: {json.dumps(data, indent=2)}")
            
    except websockets.exceptions.ConnectionClosed:
        print(f"🔌 {client_id} connection closed")
    except Exception as e:
        print(f"❌ Error receiving messages in {client_id}: {e}")

async def main():
    """Main test function"""
    print("🧪 Testing Updated Message Handling Logic")
    print("=" * 50)
    
    server_url = "ws://localhost:8000"
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            print("""
Usage: python test_message_handling.py [test_number]

Test Cases:
1. Test alert from drone (should broadcast with type='alert', single alert_id)
2. Test alert_image from application (should broadcast with type='alert_image', no schema changes)
3. Test alert_image from drone (should check name, update DB, broadcast to all)
4. Run all tests sequentially

Examples:
python test_message_handling.py 1    # Test alert handling
python test_message_handling.py 2    # Test alert_image from app
python test_message_handling.py 3    # Test alert_image from drone
python test_message_handling.py 4    # Run all tests
            """)
            return
        
        test_num = int(sys.argv[1])
    else:
        test_num = 4  # Default to all tests
    
    try:
        if test_num == 1 or test_num == 4:
            print("\n🔹 TEST 1: Alert from Drone")
            print("Expected: Store in DB, broadcast with type='alert', single alert_id outside data")
            await test_drone_client("test_drone_001", ALERT_MESSAGE, server_url)
            
            if test_num == 4:
                await asyncio.sleep(1)
        
        if test_num == 2 or test_num == 4:
            print("\n🔹 TEST 2: Alert Image from Application")
            print("Expected: Store in DB, broadcast with type='alert_image', no schema changes")
            await test_app_client("test_app_001", ALERT_IMAGE_FROM_APP, server_url)
            
            if test_num == 4:
                await asyncio.sleep(1)
        
        if test_num == 3 or test_num == 4:
            print("\n🔹 TEST 3: Alert Image from Drone (Update Existing)")
            print("Expected: Check name in DB, update if exists, broadcast to ALL clients")
            await test_drone_client("test_drone_002", ALERT_IMAGE_FROM_DRONE, server_url)
        
        print("\n✅ Test completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
