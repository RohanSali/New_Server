# Client Registry System

## Overview

Your drone alert management server **can absolutely handle multiple drones and applications simultaneously**! The client registry system provides comprehensive tracking and management of all connected clients.

## Key Features

✅ **Automatic Registration**: New clients are automatically registered when they connect  
✅ **Manual Management**: Add, remove, and update clients via CLI or API  
✅ **Authorization Control**: Authorize/deauthorize clients for security  
✅ **Real-time Tracking**: Track online/offline status and connection history  
✅ **Persistent Storage**: Client data stored in `client_registry.json`  
✅ **Export/Import**: Backup and restore client configurations  

## Quick Start

### 1. Import Sample Clients (Optional)
```bash
# Import pre-configured sample clients
python manage_clients.py import sample_clients.json
```

### 2. View All Clients
```bash
# List all registered clients
python manage_clients.py list

# List only drones
python manage_clients.py list --type drone

# List only online clients
python manage_clients.py list --status online
```

### 3. Add a New Client Manually
```bash
# Add a new drone
python manage_clients.py add drone_new_001 drone \
  --name "New Patrol Drone" \
  --description "Additional surveillance drone" \
  --capabilities alerts imaging navigation

# Add a new application
python manage_clients.py add app_monitoring application \
  --name "Monitoring App" \
  --description "Real-time monitoring dashboard"
```

### 4. View Client Details
```bash
# Show detailed information about a specific client
python manage_clients.py show drone_001
```

### 5. View Registry Statistics
```bash
# Show overall statistics
python manage_clients.py stats
```

## Multi-Client Capabilities

### Your Server Supports:
- **Unlimited concurrent drones and applications**
- **Separate connection pools** for different client types
- **Real-time broadcasting** to all connected applications
- **Individual client authorization** and access control
- **Automatic connection management** with reconnect handling

### Current Architecture:
```
                 🖥️ Server Hub (FastAPI)
                       |
          ┌─────────────┼─────────────┐
          |                          |
    🚁 Drones (N)              📱 Applications (M)
    - Send alerts              - Receive alerts
    - Receive commands         - Send responses
    - Send images             - Process data
    - Execute tasks           - Create tasks
```

## API Endpoints

### Client Management
- `GET /api/clients` - List all clients
- `GET /api/clients/{client_id}` - Get client details
- `GET /api/clients/type/{type}` - Get clients by type
- `GET /api/clients/online` - Get online clients
- `PUT /api/clients/{client_id}/authorize` - Authorize/deauthorize
- `DELETE /api/clients/{client_id}` - Remove client
- `GET /api/registry/stats` - Registry statistics

### Testing APIs
```bash
# Get all clients
curl http://localhost:8000/api/clients

# Get only drones
curl http://localhost:8000/api/clients/type/drone

# Get online clients
curl http://localhost:8000/api/clients/online

# Get registry stats
curl http://localhost:8000/api/registry/stats
```

## Command Line Management

### List Commands
```bash
# Basic listing
python manage_clients.py list
python manage_clients.py list --type drone
python manage_clients.py list --status online

# Show specific client
python manage_clients.py show drone_001
```

### Management Commands
```bash
# Add new client
python manage_clients.py add client_id type [options]

# Update client
python manage_clients.py update client_id --name "New Name"

# Authorize/deauthorize
python manage_clients.py authorize client_id
python manage_clients.py authorize client_id --deny

# Remove client
python manage_clients.py remove client_id
```

### Import/Export
```bash
# Export current registry
python manage_clients.py export
python manage_clients.py export --file my_backup.json

# Import clients
python manage_clients.py import sample_clients.json
```

## File Structure

### Generated Files:
- `client_registry.json` - Main registry database
- `client_registry.json.backup` - Automatic backup
- `clients_export_YYYYMMDD_HHMMSS.json` - Export files

### Sample Structure:
```json
{
  "drone_001": {
    "client_id": "drone_001",
    "client_type": "drone",
    "name": "Surveillance Drone Alpha",
    "status": "online",
    "capabilities": ["alerts", "imaging", "navigation"],
    "location": {"lat": 40.7128, "lng": -74.0060},
    "total_connections": 15,
    "is_authorized": true
  }
}
```

## Auto-Registration Flow

1. **Client Connects** → WebSocket connection initiated
2. **Authorization Check** → Verify if client is authorized
3. **Auto-Registration** → Register new client or update existing
4. **Connection Established** → Client receives welcome message with info
5. **Activity Tracking** → Connection count and timestamps updated
6. **Disconnection** → Status updated to offline

## Integration with Existing System

The client registry integrates seamlessly with your existing:
- **WebSocket Manager** - Auto-registers connections
- **Database** - No changes needed to your MongoDB
- **API Endpoints** - New endpoints for client management
- **Dashboard** - Can display client information

## Security Features

### Authorization Control
- New clients are authorized by default
- Can deauthorize problematic clients
- Unauthorized clients cannot connect

### Connection Tracking
- Track total connections per client
- Monitor first/last connection times
- Identify suspicious connection patterns

## Monitoring & Analytics

### Real-time Stats
```bash
=== Registry Statistics ===
Total Clients: 8
  Drones: 4
  Applications: 4
  Authorized: 8

Currently Online: 3
  Drones: 2
  Applications: 1

Registry File: client_registry.json
Last Updated: 2025-01-01 10:30:45
```

### Client Details
```bash
=== Client Details: drone_001 ===
Type: Drone
Name: Surveillance Drone Alpha
Status: Online
Authorized: Yes
Total Connections: 15
Capabilities: alerts, imaging, navigation, night_vision
Location: {'lat': 40.7128, 'lng': -74.0060, 'altitude': 100}
```

## Troubleshooting

### Common Issues:

**Client can't connect:**
- Check if client is authorized: `python manage_clients.py show client_id`
- Authorize if needed: `python manage_clients.py authorize client_id`

**Registry file corruption:**
- Restore from backup: `cp client_registry.json.backup client_registry.json`
- Re-import from export: `python manage_clients.py import backup_file.json`

**Performance with many clients:**
- The system is designed for high concurrency
- MongoDB handles the data load
- WebSocket connections are managed efficiently

## Best Practices

1. **Pre-register important clients** using the CLI or sample file
2. **Regular exports** for backup: `python manage_clients.py export`
3. **Monitor authorization status** for security
4. **Use meaningful names and descriptions** for easy identification
5. **Set appropriate capabilities** for each client type

## Next Steps

Your server is ready for multi-client operations! You can:
1. Import the sample clients or create your own
2. Start connecting multiple drones and applications
3. Monitor connections via the dashboard or API
4. Use the CLI tools for ongoing management

The system will automatically handle new connections and maintain a persistent record of all clients that have ever connected to your server.
