# Alert Flow Debug Guide

## Problem Analysis

The issue is that your application is not receiving the complete alert data from the `websockettest.py` file. Let me analyze the flow:

### Current Flow:
1. `websockettest.py` sends alert data
2. Server receives it via WebSocket
3. Server processes it in `handle_alert_from_drone`
4. Server should broadcast to all connected applications
5. Your application should receive the alert

## Fixes Applied

### 1. Enhanced Alert Handling (`websocket_manager.py`)

**Problem**: The server was trying to retrieve the alert from database immediately after insertion, which could fail due to database consistency.

**Fix**: Use the original alert data with proper serialization:

```python
# Create a properly serialized alert for broadcasting
broadcast_alert = serialize_datetime(alert_data.copy())
broadcast_alert['id'] = str(alert_id)

broadcast_message = {
    "type": "new_alert",
    "alert": broadcast_alert,
    "alert_id": str(alert_id),
    "timestamp": datetime.utcnow().isoformat()
}
```

### 2. Enhanced Debug Logging

Added comprehensive logging to track the alert flow:

```python
logger.info(f"Handling message from {client_id} (type: {client_type}): {message_type}")
logger.info(f"Message data: {json.dumps(message_data, indent=2)}")
logger.info(f"Broadcast message: {json.dumps(broadcast_message, indent=2)}")
```

### 3. Improved Serialization

Enhanced the `serialize_datetime` function to handle MongoDB Timestamp objects:

```python
elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'Timestamp':
    # Handle MongoDB Timestamp objects
    return str(obj)
```

## Testing Tools Created

### 1. `debug_alert_flow.py`
Tests the basic alert sending from drone perspective.

### 2. `debug_application_client.py`
Tests the application receiving side with detailed logging.

### 3. `test_complete_flow.py`
Tests the complete flow from drone sending to application receiving.

### 4. `test_database_connection.py`
Tests database connectivity and alert insertion.

## How to Test

### Step 1: Test Database Connection
```bash
python test_database_connection.py
```
This will verify that the database is working and alerts can be inserted.

### Step 2: Test Complete Flow
```bash
python test_complete_flow.py
```
This will test the entire flow from drone to application.

### Step 3: Debug Application Client
```bash
python debug_application_client.py
```
In one terminal, then in another:
```bash
python websockettest.py
```

### Step 4: Check Server Logs
Look for these log messages:
- "Handling message from drone_001 (type: drone): alert"
- "Processing alert from drone drone_001"
- "Alert {alert_id} from drone drone_001 processed and broadcasted"
- "Broadcast message: {...}"

## Expected Data Flow

### What `websockettest.py` sends:
```json
{
  "type": "alert",
  "data": {
    "alert": "abc!",
    "alert_location": [0.0, 0.0, 0.0],
    "timestamp": "2025-01-XX...",
    "alert_type": "Crowd",
    "score": 98.5,
    "drone_id": "drone_001"
  }
}
```

### What your application should receive:
```json
{
  "type": "new_alert",
  "alert": {
    "alert": "abc!",
    "alert_location": [0.0, 0.0, 0.0],
    "timestamp": "2025-01-XX...",
    "alert_type": "Crowd",
    "score": 98.5,
    "drone_id": "drone_001",
    "response": 0,
    "image_received": 0,
    "status": "pending",
    "id": "alert_xxxxxxxx"
  },
  "alert_id": "alert_xxxxxxxx",
  "timestamp": "2025-01-XX..."
}
```

## Troubleshooting Steps

### If Database Test Fails:
1. Check MongoDB connection string in environment variables
2. Verify database permissions
3. Check network connectivity

### If Complete Flow Test Fails:
1. Check server logs for errors
2. Verify WebSocket connections are established
3. Check if alerts are being inserted into database

### If Application Doesn't Receive Alerts:
1. Verify application is connected to correct WebSocket endpoint
2. Check if there are any serialization errors in server logs
3. Ensure the application is listening for "new_alert" message type

### If Server Logs Show Errors:
1. Look for "Object of type Timestamp is not JSON serializable" - this should be fixed
2. Check for database connection errors
3. Verify all imports are working correctly

## Key Changes Made

1. **Fixed alert broadcasting**: Now uses original alert data with proper serialization
2. **Added comprehensive logging**: To track the entire alert flow
3. **Enhanced error handling**: Better error messages and debugging info
4. **Improved serialization**: Handles MongoDB Timestamp objects properly

## Next Steps

1. Deploy the updated code to your server
2. Run the database connection test
3. Run the complete flow test
4. Test with your actual application
5. Check server logs for any remaining issues

The fixes should resolve the issue where your application wasn't receiving the complete alert data. The enhanced logging will help identify any remaining issues. 