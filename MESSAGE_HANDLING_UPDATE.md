# Updated Message Handling Logic

## Overview

The WebSocket message handling has been updated to implement specific logic for different message types as requested. Here's the complete breakdown:

## Message Handling Changes

### 1. Alert Messages from Drones (`type = 'alert'`)

**Previous Behavior**: Modified alert data and broadcast with complex schema
**New Behavior**: 
- Store alert data **as-is** in database with minimal required fields
- Broadcast with `type = 'alert'` 
- **Single `alert_id`** placed outside the data object (not inside)
- Preserve original alert schema

**Example**:
```json
// Incoming from drone:
{
  "type": "alert",
  "data": {
    "alert": "Person Detected",
    "drone_id": "drone_001",
    "alert_location": [40.7128, -74.0060, 100],
    "score": 0.85,
    "timestamp": "2025-01-01T10:00:00Z"
  }
}

// Broadcast to applications:
{
  "type": "alert",
  "alert_id": "507f1f77bcf86cd799439011",  // Single ID here
  "data": {
    "alert": "Person Detected",
    "drone_id": "drone_001", 
    "alert_location": [40.7128, -74.0060, 100],
    "score": 0.85,
    "timestamp": "2025-01-01T10:00:00Z",
    "response": 0,
    "image_received": 0,
    "status": "pending"
  },
  "timestamp": "2025-01-01T10:00:01Z"
}
```

### 2. Alert Image from Applications (`type = 'alert_image'`)

**Previous Behavior**: Modified schema and checked for drone IDs
**New Behavior**:
- Store alert image data **as-is** in database
- **No schema changes** - preserve original message structure
- **No drone ID checking**
- Broadcast with `type = 'alert_image'` to applications only
- Keep original data intact

**Example**:
```json
// Incoming from application:
{
  "type": "alert_image",
  "data": {
    "found": 1,
    "name": "person_001",
    "actual_image": "base64_data...",
    "matched_frame": "base64_data...",
    "location": [40.7128, -74.0060, 100]
  }
}

// Broadcast to applications (unchanged):
{
  "type": "alert_image",
  "data": {
    "found": 1,
    "name": "person_001",
    "actual_image": "base64_data...",
    "matched_frame": "base64_data...",
    "location": [40.7128, -74.0060, 100]
  },
  "timestamp": "2025-01-01T10:00:01Z"
}
```

### 3. Alert Image from Drones (`type = 'alert_image'`)

**Previous Behavior**: Simple storage and broadcast to applications only
**New Behavior**:
- **Check for matching 'name'** in existing database entries
- If match found: **Update existing entry** with new data
- If no match: **Create new entry**
- Broadcast with `type = 'alert_image'` to **ALL clients** (applications + drones)
- **Exclude sender drone** from broadcast
- Preserve original message schema

**Example**:
```json
// Incoming from drone:
{
  "type": "alert_image",
  "data": {
    "found": 1,
    "name": "person_001",  // This triggers name-based matching
    "drone_id": "drone_002",
    "actual_image": "updated_base64_data...",
    "confidence": 0.92
  }
}

// Database operation:
// 1. Search for existing entry with name = "person_001"
// 2. If found: UPDATE existing entry
// 3. If not found: CREATE new entry

// Broadcast to ALL clients except sender:
{
  "type": "alert_image", 
  "data": {
    "found": 1,
    "name": "person_001",
    "drone_id": "drone_002", 
    "actual_image": "updated_base64_data...",
    "confidence": 0.92
  },
  "timestamp": "2025-01-01T10:00:01Z"
}
```

## Implementation Details

### Database Operations

**Alerts Collection**: 
- Stores alerts with minimal modifications (response=0, image_received=0, status='pending')
- Returns MongoDB ObjectId as alert_id

**Alert Images Collection**:
- From Applications: Direct storage, no modifications
- From Drones: Name-based matching with update/insert logic

### Broadcasting Logic

**Applications**: 
- Receive: alerts, alert_images (from apps and drones)
- Send: responses, alert_images, processing_tasks

**Drones**:
- Receive: commands, alert_images (from other drones only)
- Send: alerts, alert_images, processing_results

### Message Routing

1. **Alert from Drone** → DB → Applications
2. **Alert Image from App** → DB → Applications  
3. **Alert Image from Drone** → DB with name check → All Clients (except sender)

## Testing

Use the provided test script to verify the logic:

```bash
# Test alert handling
python test_message_handling.py 1

# Test alert_image from application  
python test_message_handling.py 2

# Test alert_image from drone with name matching
python test_message_handling.py 3

# Run all tests
python test_message_handling.py 4
```

## Key Improvements

✅ **Alert ID Fix**: Single alert_id placement outside data object  
✅ **Schema Preservation**: Original message schemas maintained  
✅ **Smart Database Updates**: Name-based matching for alert images from drones  
✅ **Comprehensive Broadcasting**: Alert images from drones reach all relevant clients  
✅ **No Unintended Modifications**: Messages broadcast exactly as intended  

## Migration Notes

- Existing clients will receive messages in the updated format
- Alert processing applications should expect `alert_id` at the root level
- Drone alert image processing now updates existing entries by name
- All clients now receive drone alert images for better coordination
