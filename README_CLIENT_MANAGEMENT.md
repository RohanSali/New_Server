# Client Management System - Complete Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Client Registration](#client-registration)
- [Authorization Management](#authorization-management)
- [Client Information & Monitoring](#client-information--monitoring)
- [Import/Export Operations](#importexport-operations)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## 🌟 Overview

The Client Management System provides comprehensive tracking and management of all drones and applications connecting to your server. It offers both command-line tools and REST API endpoints for complete control over client access and monitoring.

### Key Features
- ✅ **Automatic Registration**: New clients auto-register when they connect
- ✅ **Authorization Control**: Approve/deny client access for security
- ✅ **Real-time Tracking**: Monitor online/offline status and connection history
- ✅ **Persistent Storage**: Client data stored in `client_registry.json`
- ✅ **Import/Export**: Backup and restore client configurations
- ✅ **CLI & API**: Command-line tools and REST API endpoints

---

## 🚀 Quick Start

### 1. Import Sample Clients (Recommended for Testing)
```bash
# Import 8 pre-configured clients (4 drones + 4 applications)
python manage_clients.py import sample_clients.json

# Verify import was successful
python manage_clients.py list
```

### 2. Check System Status
```bash
# View registry statistics
python manage_clients.py stats

# List all registered clients
python manage_clients.py list
```

### 3. Test Connection
Your clients should now be able to connect. Try connecting with any of these pre-configured IDs:
- **Drones**: `drone_001`, `drone_002`, `drone_003`, `drone_emergency_001`
- **Applications**: `app_security_center`, `app_ai_analyzer`, `app_mobile_dashboard`, `app_data_logger`

---

## 👥 Client Registration

### Adding New Clients Manually

#### Basic Client Addition
```bash
# Add a drone
python manage_clients.py add my_drone_001 drone

# Add an application
python manage_clients.py add my_app_001 application
```

#### Advanced Client Addition with Details
```bash
# Add drone with full details
python manage_clients.py add patrol_drone_alpha drone \
  --name "Patrol Drone Alpha" \
  --description "Primary security patrol drone" \
  --capabilities alerts imaging navigation night_vision \
  --location '{"lat": 40.7128, "lng": -74.0060, "altitude": 100}'

# Add application with details
python manage_clients.py add monitoring_app application \
  --name "Security Monitoring App" \
  --description "Real-time security monitoring dashboard" \
  --capabilities monitoring analysis response incident_management
```

### Automatic Registration
When a client connects via WebSocket, it's automatically registered if not already present:
```
Client connects → Auto-registration → Authorization check → Connection established
```

### Removing Clients
```bash
# Remove a specific client completely
python manage_clients.py remove my_drone_001

# This permanently deletes the client from registry
```

---

## 🔐 Authorization Management

### Understanding Authorization
- **New clients** are **authorized by default** for easy development
- **Deauthorized clients** cannot connect to the server
- Authorization can be changed at any time

### Authorization Commands

#### Authorize a Client
```bash
# Authorize a client (allow connections)
python manage_clients.py authorize drone_001

# Verify authorization status
python manage_clients.py show drone_001
```

#### Deauthorize a Client
```bash
# Deauthorize a client (block connections)
python manage_clients.py authorize drone_001 --deny

# Client will be disconnected and cannot reconnect
```

#### Check Authorization Status
```bash
# View client details including authorization
python manage_clients.py show drone_001

# List all clients with authorization status
python manage_clients.py list
```

### Authorization Scenarios

#### Scenario 1: Block a Problematic Client
```bash
# Identify problematic client
python manage_clients.py show suspicious_drone

# Deauthorize immediately
python manage_clients.py authorize suspicious_drone --deny

# Client will be disconnected and blocked
```

#### Scenario 2: Temporary Access Control
```bash
# Deauthorize for maintenance
python manage_clients.py authorize maintenance_drone --deny

# Re-authorize when ready
python manage_clients.py authorize maintenance_drone
```

---

## 📊 Client Information & Monitoring

### Viewing Client Information

#### List All Clients
```bash
# Basic list
python manage_clients.py list

# Example output:
# Client ID     | Type | Name           | Status | Connections | Last Connected | Authorized
# drone_001     | Drone| Patrol Alpha   | Online | 5           | 2025-01-01     | ✓
# app_monitor   | App  | Monitor App    | Offline| 12          | 2025-01-01     | ✓
```

#### Filter Client Lists
```bash
# List only drones
python manage_clients.py list --type drone

# List only applications
python manage_clients.py list --type application

# List only online clients
python manage_clients.py list --status online

# List only offline clients
python manage_clients.py list --status offline
```

#### Detailed Client Information
```bash
# View complete details for a specific client
python manage_clients.py show drone_001

# Example output:
# === Client Details: drone_001 ===
# Type: Drone
# Name: Surveillance Drone Alpha
# Status: Online
# Authorized: Yes
# Total Connections: 15
# Capabilities: alerts, imaging, navigation
# Location: {'lat': 40.7128, 'lng': -74.0060}
# Metadata: {...}
```

### Registry Statistics
```bash
# View system-wide statistics
python manage_clients.py stats

# Example output:
# === Registry Statistics ===
# Total Clients: 10
#   Drones: 6
#   Applications: 4
#   Authorized: 10
# 
# Currently Online: 3
#   Drones: 2
#   Applications: 1
```

### Monitoring Connection Activity

#### Real-time Connection Monitoring
- **Online Status**: Updated when clients connect/disconnect
- **Connection Count**: Tracks total lifetime connections per client
- **Last Connected**: Records timestamp of last connection
- **First Connected**: Records when client first connected

#### Connection History
```bash
# View client's connection history
python manage_clients.py show drone_001

# Check which clients are currently online
python manage_clients.py list --status online
```

---

## 💾 Import/Export Operations

### Exporting Client Data

#### Basic Export
```bash
# Export all clients to timestamped file
python manage_clients.py export

# Output: clients_export_20250101_103045.json
```

#### Custom Export Location
```bash
# Export to specific file
python manage_clients.py export --file my_client_backup.json
```

### Importing Client Data

#### Import from File
```bash
# Import clients from exported file
python manage_clients.py import my_client_backup.json

# Import sample configuration
python manage_clients.py import sample_clients.json
```

### Backup Strategies

#### Regular Backup
```bash
# Create daily backup
python manage_clients.py export --file "backup_$(date +%Y%m%d).json"
```

#### Pre-deployment Backup
```bash
# Before making changes
python manage_clients.py export --file pre_deployment_backup.json

# Make your changes...

# Restore if needed
python manage_clients.py import pre_deployment_backup.json
```

---

## 🌐 API Endpoints

### Client Information APIs

#### Get All Clients
```bash
curl http://localhost:8000/api/clients

# Response:
# {
#   "clients": {...},
#   "count": 10
# }
```

#### Get Specific Client
```bash
curl http://localhost:8000/api/clients/drone_001

# Response includes all client details
```

#### Filter by Type
```bash
# Get all drones
curl http://localhost:8000/api/clients/type/drone

# Get all applications  
curl http://localhost:8000/api/clients/type/application
```

#### Get Online Clients
```bash
curl http://localhost:8000/api/clients/online
```

### Management APIs

#### Authorize Client
```bash
# Authorize a client
curl -X PUT "http://localhost:8000/api/clients/drone_001/authorize?authorized=true"

# Deauthorize a client
curl -X PUT "http://localhost:8000/api/clients/drone_001/authorize?authorized=false"
```

#### Remove Client
```bash
# Permanently remove client
curl -X DELETE http://localhost:8000/api/clients/drone_001
```

#### Registry Statistics
```bash
curl http://localhost:8000/api/registry/stats

# Response includes counts, online status, etc.
```

### API Response Examples

#### Client Details Response
```json
{
  "client_id": "drone_001",
  "client_type": "drone", 
  "name": "Surveillance Drone Alpha",
  "description": "Primary surveillance drone",
  "capabilities": ["alerts", "imaging", "navigation"],
  "location": {"lat": 40.7128, "lng": -74.0060},
  "status": "online",
  "total_connections": 15,
  "is_authorized": true,
  "first_connected": "2025-01-01T10:00:00Z",
  "last_connected": "2025-01-01T15:30:00Z"
}
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue: Client Cannot Connect
```
ERROR: Unauthorized connection attempt: my_drone
```

**Solutions:**
```bash
# Check if client exists and is authorized
python manage_clients.py show my_drone

# If not found, add the client
python manage_clients.py add my_drone drone --name "My Drone"

# If found but not authorized, authorize it
python manage_clients.py authorize my_drone
```

#### Issue: Registry File Corruption
```
ERROR: Error loading client registry: Invalid JSON
```

**Solutions:**
```bash
# Restore from automatic backup
cp client_registry.json.backup client_registry.json

# Or import from export file
python manage_clients.py import my_backup.json

# Or start fresh with samples
python manage_clients.py import sample_clients.json
```

#### Issue: Client Shows as Offline but Should be Online
**Diagnosis:**
```bash
# Check client status
python manage_clients.py show problematic_client

# Check registry stats
python manage_clients.py stats
```

**Solutions:**
- Client may have disconnected unexpectedly
- Check server logs for connection errors
- Client will auto-update to online when it reconnects

#### Issue: Too Many Unauthorized Connections
**Solutions:**
```bash
# List all unauthorized clients
python manage_clients.py list | grep "✗"

# Bulk authorize if legitimate
python manage_clients.py authorize client_1
python manage_clients.py authorize client_2

# Or remove if not legitimate
python manage_clients.py remove suspicious_client
```

### Debugging Commands

#### Verify Registry Integrity
```bash
# Check registry stats
python manage_clients.py stats

# List all clients to verify data
python manage_clients.py list

# Check specific client details
python manage_clients.py show suspicious_client
```

#### Monitor Connection Issues
```bash
# Watch server logs while client connects
tail -f server.log

# Check API endpoint
curl http://localhost:8000/api/clients/online

# Test client authorization
curl http://localhost:8000/api/clients/test_client
```

---

## ✨ Best Practices

### Development Environment

#### Quick Setup for Testing
```bash
# Import sample clients for immediate testing
python manage_clients.py import sample_clients.json

# Your test clients can connect immediately:
# - drone_001, drone_002, drone_003
# - app_security_center, app_ai_analyzer
```

#### Custom Test Clients
```bash
# Add your specific test clients
python manage_clients.py add test_drone_dev drone --name "Development Test Drone"
python manage_clients.py add test_app_dev application --name "Development Test App"
```

### Production Environment

#### Pre-register Production Clients
```bash
# Add production clients before deployment
python manage_clients.py add prod_drone_01 drone \
  --name "Production Drone 01" \
  --description "Primary production surveillance drone" \
  --capabilities alerts imaging navigation emergency_response

# Export configuration for deployment
python manage_clients.py export --file production_clients.json
```

#### Security Practices
```bash
# Regular audit of authorized clients
python manage_clients.py list | grep "✓" | wc -l

# Remove decommissioned clients
python manage_clients.py remove old_drone_001

# Regular backups
python manage_clients.py export --file "backup_$(date +%Y%m%d).json"
```

### Monitoring & Maintenance

#### Regular Health Checks
```bash
# Daily status check
python manage_clients.py stats

# Weekly client audit
python manage_clients.py list --status offline | grep "Never"  # Never connected clients

# Monthly backup
python manage_clients.py export --file "monthly_backup_$(date +%Y%m).json"
```

#### Performance Optimization
- **Remove unused clients** that never connect
- **Export/import** for database cleanup if registry grows large  
- **Monitor connection patterns** for unusual activity

### Integration Patterns

#### Automated Client Management
```bash
# Script to auto-add clients from config file
while IFS= read -r client_id; do
  python manage_clients.py add "$client_id" drone --name "Auto Added Drone $client_id"
done < drone_list.txt
```

#### API Integration
```python
import requests

# Python script to manage clients via API
def authorize_client(client_id, authorized=True):
    response = requests.put(
        f"http://localhost:8000/api/clients/{client_id}/authorize",
        params={"authorized": authorized}
    )
    return response.json()

# Usage
authorize_client("new_drone_001", True)
```

---

## 📁 File Reference

### Generated Files
- `client_registry.json` - Main client database
- `client_registry.json.backup` - Automatic backup
- `clients_export_YYYYMMDD_HHMMSS.json` - Export files
- `sample_clients.json` - Pre-configured sample clients

### Commands Reference
```bash
# Management
python manage_clients.py list [--type TYPE] [--status STATUS]
python manage_clients.py show CLIENT_ID
python manage_clients.py add CLIENT_ID TYPE [options]
python manage_clients.py remove CLIENT_ID
python manage_clients.py update CLIENT_ID [options]

# Authorization  
python manage_clients.py authorize CLIENT_ID [--deny]

# Data Operations
python manage_clients.py import FILE
python manage_clients.py export [--file FILE]
python manage_clients.py stats
```

### API Endpoints Reference
```
GET    /api/clients                    # List all clients
GET    /api/clients/{client_id}        # Get client details  
GET    /api/clients/type/{type}        # Get clients by type
GET    /api/clients/online             # Get online clients
PUT    /api/clients/{id}/authorize     # Authorize/deauthorize
DELETE /api/clients/{client_id}        # Remove client
GET    /api/registry/stats             # Get statistics
```

---

## 🎯 Summary

The Client Management System provides complete control over your drone and application clients with:

- **Easy Setup**: Import samples or add clients manually
- **Flexible Authorization**: Allow/block clients as needed
- **Comprehensive Monitoring**: Track connections, status, and history
- **Data Safety**: Automatic backups and import/export capabilities
- **Multiple Interfaces**: CLI tools and REST API endpoints
- **Production Ready**: Suitable for development and production environments

Your server can handle unlimited concurrent clients with full management capabilities!

---

*For more information, see the additional documentation files:*
- `CLIENT_REGISTRY_README.md` - Detailed technical documentation
- `MESSAGE_HANDLING_UPDATE.md` - WebSocket message handling details
