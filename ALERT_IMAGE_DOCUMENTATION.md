# Alert Image Functionality Documentation

## Overview

The Alert Image functionality allows drones to send captured images with detection results to the server. This includes both the actual captured image and a matched reference frame, along with metadata about the detection.

## Database Schema

### Collection: `alertImage`

The `alertImage` collection stores alert image records with the following schema:

```json
{
  "_id": "ObjectId",
  "found": 1,                    // Detection status (1=found, 0=not found)
  "name": "Person Detected",      // Name or identifier of detected object
  "drone_id": "Drone001",        // ID of the drone that captured the image
  "actual_image": "base64_blob", // Base64 encoded actual image
  "matched_frame": "base64_blob", // Base64 encoded matched reference frame
  "location": [10.5, 20.3, 5.0], // Location coordinates [x, y, z]
  "timestamp": "2024-01-01T12:00:00Z", // Capture timestamp in ISO format
  "created_at": "2024-01-01T12:00:00Z" // Record creation timestamp
}
```

## REST API Endpoints

### 1. Create Alert Image
**POST** `/api/alert-images`

Creates a new alert image record.

**Request Body:**
```json
{
  "found": 1,
  "name": "Person Detected",
  "drone_id": "Drone001",
  "actual_image": "base64_encoded_image_blob",
  "matched_frame": "base64_encoded_reference_blob",
  "location": [10.5, 20.3, 5.0],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Response:**
```json
{
  "alert_image_id": "507f1f77bcf86cd799439011",
  "message": "Alert image created successfully"
}
```

### 2. Get All Alert Images
**GET** `/api/alert-images?limit=100`

Retrieves all alert images with optional limit parameter.

**Response:**
```json
{
  "alert_images": [
    {
      "id": "507f1f77bcf86cd799439011",
      "found": 1,
      "name": "Person Detected",
      "drone_id": "Drone001",
      "actual_image": "base64_blob",
      "matched_frame": "base64_blob",
      "location": [10.5, 20.3, 5.0],
      "timestamp": "2024-01-01T12:00:00Z",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 1
}
```

### 3. Get Specific Alert Image
**GET** `/api/alert-images/{alert_image_id}`

Retrieves a specific alert image by ID.

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "found": 1,
  "name": "Person Detected",
  "drone_id": "Drone001",
  "actual_image": "base64_blob",
  "matched_frame": "base64_blob",
  "location": [10.5, 20.3, 5.0],
  "timestamp": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### 4. Get Alert Images by Drone
**GET** `/api/alert-images/drone/{drone_id}?limit=50`

Retrieves alert images for a specific drone.

**Response:**
```json
{
  "alert_images": [...],
  "count": 5,
  "drone_id": "Drone001"
}
```

### 5. Delete Alert Image
**DELETE** `/api/alert-images/{alert_image_id}`

Deletes a specific alert image by ID.

**Response:**
```json
{
  "message": "Alert image deleted successfully"
}
```

## WebSocket Endpoints

### Drone WebSocket
**WebSocket** `/ws/drone/{drone_id}`

Drones can send alert image data via WebSocket.

**Message Format:**
```json
{
  "type": "alert_image",
  "data": {
    "found": 1,
    "name": "Person Detected",
    "drone_id": "Drone001",
    "actual_image": "base64_blob",
    "matched_frame": "base64_blob",
    "location": [10.5, 20.3, 5.0],
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Application WebSocket
**WebSocket** `/ws/application/{app_id}`

Applications receive real-time notifications when alert images are received.

**Notification Message:**
```json
{
  "type": "alert_image_received",
  "alert_image_id": "507f1f77bcf86cd799439011",
  "alert_image": {
    "found": 1,
    "name": "Person Detected",
    "drone_id": "Drone001",
    "actual_image": "base64_blob",
    "matched_frame": "base64_blob",
    "location": [10.5, 20.3, 5.0],
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "drone_id": "Drone001",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Usage Examples

### Python Client Example

```python
import requests
import json
import base64

# Create alert image
alert_image_data = {
    "found": 1,
    "name": "Person Detected",
    "drone_id": "Drone001",
    "actual_image": base64.b64encode(actual_image_bytes).decode('utf-8'),
    "matched_frame": base64.b64encode(reference_image_bytes).decode('utf-8'),
    "location": [10.5, 20.3, 5.0],
    "timestamp": "2024-01-01T12:00:00Z"
}

response = requests.post("http://localhost:8000/api/alert-images", json=alert_image_data)
print(response.json())
```

### WebSocket Client Example

```python
import asyncio
import websockets
import json

async def send_alert_image():
    uri = "ws://localhost:8000/ws/drone/Drone001"
    async with websockets.connect(uri) as websocket:
        # Send alert image
        message = {
            "type": "alert_image",
            "data": {
                "found": 1,
                "name": "Person Detected",
                "drone_id": "Drone001",
                "actual_image": "base64_blob",
                "matched_frame": "base64_blob",
                "location": [10.5, 20.3, 5.0],
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
        await websocket.send(json.dumps(message))

asyncio.run(send_alert_image())
```

## Database Indexes

The following indexes are automatically created for the `alertImage` collection:

- `drone_id` - For efficient queries by drone
- `timestamp` - For time-based queries
- `found` - For filtering by detection status
- `name` - For filtering by object name

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid data)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

## Testing

Use the provided test script to verify functionality:

```bash
python test_alert_images.py
```

This script tests both REST API and WebSocket functionality.

## Configuration

The alert image collection is configured in `config.py`:

```python
ALERT_IMAGES_COLLECTION = "alertImage"
```

## Security Considerations

1. **Image Size**: Large base64 encoded images may impact performance
2. **Storage**: Consider implementing image compression or external storage for large images
3. **Authentication**: Consider adding authentication for production use
4. **Rate Limiting**: Implement rate limiting for high-frequency image uploads

## Performance Notes

1. **Indexing**: Database indexes are created automatically for efficient queries
2. **Serialization**: Images are stored as base64 strings for easy JSON serialization
3. **Real-time**: WebSocket notifications provide real-time updates to applications
4. **Scalability**: The system can handle multiple drones and applications simultaneously 