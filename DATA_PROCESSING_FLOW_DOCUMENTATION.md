# Data Processing Flow Documentation

## Overview

The Data Processing Flow enables applications to send processing tasks to drones, which then process the data and return results. This creates a complete cycle:

1. **Application** sends initial data/processing task to server
2. **Server** forwards the task to the target **Drone**
3. **Drone** processes the data and sends results back to server
4. **Application** receives the updated/processed data from server

## Database Schema

### Collection: `processingTasks`

Stores processing tasks created by applications:

```json
{
  "_id": "ObjectId",
  "task_id": "task_abc12345",
  "app_id": "App001",
  "drone_id": "Drone001",
  "task_type": "image_analysis",
  "input_data": {
    "image_url": "https://example.com/image.jpg",
    "parameters": {
      "confidence_threshold": 0.8,
      "max_objects": 10
    }
  },
  "status": "pending",
  "priority": 3,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### Collection: `processingResults`

Stores results returned by drones:

```json
{
  "_id": "ObjectId",
  "task_id": "task_abc12345",
  "drone_id": "Drone001",
  "result_data": {
    "detected_objects": [
      {
        "type": "person",
        "confidence": 0.95,
        "bbox": [100, 200, 150, 300]
      }
    ],
    "processing_metadata": {
      "processing_time_ms": 1250,
      "algorithm_version": "v2.1"
    }
  },
  "processing_time": 1.25,
  "success": true,
  "error_message": null,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## REST API Endpoints

### Processing Tasks

#### 1. Create Processing Task
**POST** `/api/processing-tasks`

Creates a new processing task.

**Request Body:**
```json
{
  "app_id": "App001",
  "drone_id": "Drone001",
  "task_type": "image_analysis",
  "input_data": {
    "image_url": "https://example.com/image.jpg",
    "analysis_type": "object_detection",
    "parameters": {
      "confidence_threshold": 0.8,
      "max_objects": 10
    }
  },
  "priority": 3
}
```

**Response:**
```json
{
  "task_id": "task_abc12345",
  "message": "Processing task created successfully"
}
```

#### 2. Get Processing Task
**GET** `/api/processing-tasks/{task_id}`

Retrieves a specific processing task.

**Response:**
```json
{
  "task_id": "task_abc12345",
  "app_id": "App001",
  "drone_id": "Drone001",
  "task_type": "image_analysis",
  "input_data": {...},
  "status": "pending",
  "priority": 3,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### 3. Get Pending Tasks for Drone
**GET** `/api/processing-tasks/drone/{drone_id}/pending?limit=10`

Retrieves pending tasks for a specific drone.

**Response:**
```json
{
  "tasks": [...],
  "count": 5,
  "drone_id": "Drone001"
}
```

### Processing Results

#### 1. Get Processing Result
**GET** `/api/processing-results/{task_id}`

Retrieves processing result by task ID.

**Response:**
```json
{
  "task_id": "task_abc12345",
  "drone_id": "Drone001",
  "result_data": {
    "detected_objects": [...],
    "processing_metadata": {...}
  },
  "processing_time": 1.25,
  "success": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 2. Get Results by Drone
**GET** `/api/processing-results/drone/{drone_id}?limit=50`

Retrieves all processing results for a specific drone.

**Response:**
```json
{
  "results": [...],
  "count": 10,
  "drone_id": "Drone001"
}
```

## WebSocket Endpoints

### Application WebSocket
**WebSocket** `/ws/application/{app_id}`

Applications can send processing tasks and receive results.

#### Sending Processing Task
```json
{
  "type": "processing_task",
  "data": {
    "app_id": "App001",
    "drone_id": "Drone001",
    "task_type": "object_detection",
    "input_data": {
      "image_data": "base64_encoded_image",
      "detection_parameters": {
        "min_confidence": 0.7,
        "max_objects": 5
      }
    },
    "priority": 2
  }
}
```

#### Receiving Processing Result
```json
{
  "type": "processing_result_received",
  "result_id": "507f1f77bcf86cd799439011",
  "task_id": "task_abc12345",
  "result_data": {
    "detections": [
      {
        "class": "person",
        "confidence": 0.92,
        "bbox": [50, 100, 200, 400]
      }
    ],
    "processing_info": {
      "algorithm": "YOLOv5",
      "processing_time_ms": 850
    }
  },
  "drone_id": "Drone001",
  "app_id": "App001",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Receiving Task Status Update
```json
{
  "type": "task_status_update",
  "task_id": "task_abc12345",
  "status": "processing",
  "drone_id": "Drone001",
  "additional_data": {
    "progress": 50
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Drone WebSocket
**WebSocket** `/ws/drone/{drone_id}`

Drones receive processing tasks and send results.

#### Receiving Processing Task
```json
{
  "type": "processing_task",
  "task_id": "task_abc12345",
  "task_data": {
    "app_id": "App001",
    "drone_id": "Drone001",
    "task_type": "object_detection",
    "input_data": {...},
    "priority": 2
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Sending Processing Result
```json
{
  "type": "processing_result",
  "data": {
    "task_id": "task_abc12345",
    "drone_id": "Drone001",
    "result_data": {
      "detections": [...],
      "processing_info": {...}
    },
    "processing_time": 0.85,
    "success": true,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### Sending Task Status Update
```json
{
  "type": "task_status_update",
  "data": {
    "task_id": "task_abc12345",
    "status": "processing",
    "additional_data": {
      "progress": 75
    }
  }
}
```

## Complete Flow Example

### Step 1: Application Creates Task
```python
import requests
import json

# Application creates a processing task
task_data = {
    "app_id": "App001",
    "drone_id": "Drone001",
    "task_type": "image_analysis",
    "input_data": {
        "image_url": "https://example.com/image.jpg",
        "analysis_type": "object_detection"
    },
    "priority": 2
}

response = requests.post("http://localhost:8000/api/processing-tasks", json=task_data)
task_id = response.json()["task_id"]
print(f"Task created: {task_id}")
```

### Step 2: Drone Receives Task (WebSocket)
```python
import asyncio
import websockets
import json

async def drone_worker():
    uri = "ws://localhost:8000/ws/drone/Drone001"
    async with websockets.connect(uri) as websocket:
        # Wait for processing task
        message = await websocket.recv()
        data = json.loads(message)
        
        if data["type"] == "processing_task":
            task_id = data["task_id"]
            task_data = data["task_data"]
            
            # Process the task
            result = await process_image(task_data["input_data"])
            
            # Send result back
            result_message = {
                "type": "processing_result",
                "data": {
                    "task_id": task_id,
                    "drone_id": "Drone001",
                    "result_data": result,
                    "processing_time": 1.25,
                    "success": True,
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            }
            await websocket.send(json.dumps(result_message))

asyncio.run(drone_worker())
```

### Step 3: Application Receives Result (WebSocket)
```python
import asyncio
import websockets
import json

async def application_worker():
    uri = "ws://localhost:8000/ws/application/App001"
    async with websockets.connect(uri) as websocket:
        # Send processing task
        task_message = {
            "type": "processing_task",
            "data": {
                "app_id": "App001",
                "drone_id": "Drone001",
                "task_type": "image_analysis",
                "input_data": {"image_url": "https://example.com/image.jpg"},
                "priority": 2
            }
        }
        await websocket.send(json.dumps(task_message))
        
        # Wait for result
        message = await websocket.recv()
        data = json.loads(message)
        
        if data["type"] == "processing_result_received":
            result_data = data["result_data"]
            print(f"Received result: {result_data}")

asyncio.run(application_worker())
```

## Task Status Flow

Tasks go through the following status progression:

1. **pending** - Task created, waiting for drone to pick up
2. **processing** - Drone is actively processing the task
3. **completed** - Task completed successfully
4. **failed** - Task failed (with error message)

## Priority System

Tasks have a priority level (1-5):
- **1** - Low priority
- **2** - Normal priority
- **3** - High priority
- **4** - Urgent priority
- **5** - Critical priority

Drones process tasks in priority order (highest first), then by creation time.

## Error Handling

### Failed Tasks
If a drone encounters an error during processing:

```json
{
  "type": "processing_result",
  "data": {
    "task_id": "task_abc12345",
    "drone_id": "Drone001",
    "result_data": {},
    "processing_time": 0.5,
    "success": false,
    "error_message": "Image processing failed: Invalid image format",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Timeout Handling
- Tasks that remain pending for too long can be marked as failed
- Applications should implement retry logic for failed tasks
- Consider implementing task timeout configuration

## Best Practices

### For Applications
1. **Task Design**: Keep input data concise and well-structured
2. **Error Handling**: Always check the `success` field in results
3. **Retry Logic**: Implement retry mechanisms for failed tasks
4. **Monitoring**: Track task status updates for progress monitoring
5. **Resource Management**: Don't overwhelm drones with too many concurrent tasks

### For Drones
1. **Status Updates**: Send regular status updates during long processing
2. **Error Reporting**: Provide detailed error messages for debugging
3. **Resource Management**: Implement task queuing and processing limits
4. **Result Format**: Ensure consistent result data structure
5. **Performance**: Monitor processing times and optimize algorithms

## Testing

Use the provided test script to verify the complete flow:

```bash
python test_data_processing_flow.py
```

This script tests both REST API and WebSocket functionality for the complete data processing cycle.

## Configuration

The processing collections are configured in `config.py`:

```python
PROCESSING_TASKS_COLLECTION = "processingTasks"
PROCESSING_RESULTS_COLLECTION = "processingResults"
```

## Database Indexes

The following indexes are automatically created:

**Processing Tasks:**
- `task_id` (unique) - For efficient task lookup
- `app_id` - For filtering by application
- `drone_id` - For filtering by drone
- `status` - For filtering by status
- `created_at` - For time-based queries

**Processing Results:**
- `task_id` (unique) - For efficient result lookup
- `drone_id` - For filtering by drone
- `timestamp` - For time-based queries

## Security Considerations

1. **Authentication**: Consider adding authentication for production use
2. **Authorization**: Implement role-based access control
3. **Data Validation**: Validate all input data and results
4. **Rate Limiting**: Implement rate limiting for task creation
5. **Resource Limits**: Set maximum task size and processing time limits 