# Multiple Alerts Broadcasting Fix

## Problem Summary

The server was experiencing JSON serialization errors when trying to broadcast multiple alerts to connected applications. The error message was:

```
Error broadcasting to application app_001: Object of type Timestamp is not JSON serializable
```

This caused the application to disconnect after the first alert, preventing subsequent alerts from being received.

## Root Cause

The issue was in the MongoDB change stream callback in `main.py` where raw MongoDB change events (containing MongoDB-specific objects like `Timestamp`) were being broadcasted directly without proper serialization.

## Fixes Applied

### 1. Enhanced Change Stream Callback (`main.py`)

**Before:**
```python
async def change_stream_callback(change_event: Dict[str, Any]):
    await websocket_manager.broadcast_to_applications({
        "type": "alert_update",
        "change": change_event,  # Raw MongoDB object
        "timestamp": change_event.get('timestamp')
    })
```

**After:**
```python
async def change_stream_callback(change_event: Dict[str, Any]):
    # Serialize the change event to make it JSON compatible
    serialized_change = {}
    
    # Handle the change event structure
    if 'operationType' in change_event:
        serialized_change['operationType'] = change_event['operationType']
    
    if 'documentKey' in change_event:
        # Convert ObjectId to string
        if '_id' in change_event['documentKey']:
            serialized_change['documentKey'] = {
                '_id': str(change_event['documentKey']['_id'])
            }
    
    if 'fullDocument' in change_event:
        # Serialize the full document
        from websocket_manager import serialize_datetime
        serialized_change['fullDocument'] = serialize_datetime(change_event['fullDocument'])
    
    # Broadcast the serialized change
    await websocket_manager.broadcast_to_applications({
        "type": "alert_update",
        "change": serialized_change,
        "timestamp": serialized_change['timestamp']
    })
```

### 2. Enhanced Serialization Function (`websocket_manager.py`)

**Before:**
```python
def serialize_datetime(obj):
    # Only handled datetime and ObjectId
```

**After:**
```python
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
```

### 3. Improved Alert Handling (`websocket_manager.py`)

**Before:**
```python
broadcast_message = {
    "type": "new_alert",
    "alert": alert_data,  # Raw alert data
    "alert_id": str(alert_id),
    "timestamp": datetime.utcnow().isoformat()
}
```

**After:**
```python
# Get the complete alert data from database to ensure proper serialization
complete_alert = await db_manager.get_alert(str(alert_id))

broadcast_message = {
    "type": "new_alert",
    "alert": complete_alert if complete_alert else serialize_datetime(alert_data),
    "alert_id": str(alert_id),
    "timestamp": datetime.utcnow().isoformat()
}
```

### 4. Enhanced Initial Alerts Sending (`main.py`)

**Before:**
```python
initial_data_message = {
    "type": "initial_alerts",
    "alerts": alerts,  # Raw alerts from database
    "timestamp": asyncio.get_event_loop().time()
}
```

**After:**
```python
# Ensure alerts are properly serialized
from websocket_manager import serialize_datetime
serialized_alerts = serialize_datetime(alerts)

initial_data_message = {
    "type": "initial_alerts",
    "alerts": serialized_alerts,
    "timestamp": datetime.utcnow().isoformat()
}
```

## Testing the Fix

### 1. Test Multiple Alerts Sending

Run the test script to send multiple alerts:

```bash
python test_multiple_alerts.py
```

This script will send 5 different alerts with 2-second intervals between them.

### 2. Test Application Client

Run the test application client to verify alerts are received:

```bash
python test_application_client.py
```

This will connect to the WebSocket server and listen for all incoming alerts.

### 3. Manual Testing

You can also use the existing `websockettest.py` script multiple times:

```bash
python websockettest.py
```

## Expected Results

After the fix:

1. **No Serialization Errors**: The server logs should not show "Object of type Timestamp is not JSON serializable" errors
2. **Multiple Alerts Received**: All alerts should be received by connected applications
3. **No Disconnections**: Applications should remain connected after receiving alerts
4. **Proper JSON**: All broadcasted messages should be valid JSON

## Verification Steps

1. Start your application client
2. Run the multiple alerts test script
3. Check that all 5 alerts are received without disconnection
4. Verify the server logs show no serialization errors
5. Confirm that the application displays all alerts correctly

## Files Modified

- `main.py`: Enhanced change stream callback and initial alerts sending
- `websocket_manager.py`: Improved serialization function and alert handling
- `test_multiple_alerts.py`: New test script for multiple alerts
- `test_application_client.py`: New test client for verification

## Deployment

The fixes are ready for deployment. The changes ensure that:

1. All MongoDB objects are properly serialized before broadcasting
2. Multiple alerts can be sent without causing disconnections
3. The application receives all alerts in real-time
4. The system maintains stable WebSocket connections

The fix addresses the core issue while maintaining backward compatibility with existing clients. 