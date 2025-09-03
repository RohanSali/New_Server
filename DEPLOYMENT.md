# 🚀 Deployment Guide - Drone Alert Management System

This guide will help you deploy your drone alert management system to the internet so it can be accessed from anywhere.

## 🌐 Deployment Options

### Option 1: Railway (Recommended - Easy & Free)

**Railway** is the easiest option with a generous free tier.

#### Step 1: Prepare Your Code
1. Make sure all files are committed to a Git repository
2. Ensure you have the following files in your root directory:
   - `requirements.txt`
   - `Procfile`
   - `railway.json`
   - `main_production.py`

#### Step 2: Set Up Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect it's a Python app

#### Step 3: Configure Environment Variables
In Railway dashboard, go to your project → Variables tab and add:

```bash
MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/drone_alerts_db?retryWrites=true&w=majority
DATABASE_NAME=drone_alerts_db
ENVIRONMENT=production
DEBUG=false
PORT=8000
HOST=0.0.0.0
```

#### Step 4: Set Up MongoDB Atlas (Free Cloud Database)
1. Go to [mongodb.com/atlas](https://mongodb.com/atlas)
2. Create a free account
3. Create a new cluster (free tier)
4. Create a database user
5. Get your connection string
6. Add it to Railway environment variables

#### Step 5: Deploy
1. Railway will automatically deploy when you push to GitHub
2. Your app will be available at: `https://your-app-name.railway.app`

---

### Option 2: Render (Free Tier Available)

#### Step 1: Prepare for Render
Create a `render.yaml` file:

```yaml
services:
  - type: web
    name: drone-alert-system
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main_production.py
    envVars:
      - key: MONGODB_URI
        value: mongodb+srv://your_username:your_password@your_cluster.mongodb.net/drone_alerts_db?retryWrites=true&w=majority
      - key: DATABASE_NAME
        value: drone_alerts_db
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
```

#### Step 2: Deploy to Render
1. Go to [render.com](https://render.com)
2. Connect your GitHub repository
3. Create a new Web Service
4. Configure environment variables
5. Deploy

---

### Option 3: Heroku (Paid)

#### Step 1: Install Heroku CLI
```bash
# Windows
winget install --id=Heroku.HerokuCLI

# macOS
brew tap heroku/brew && brew install heroku
```

#### Step 2: Deploy
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-drone-alert-app

# Add MongoDB addon
heroku addons:create mongolab:sandbox

# Set environment variables
heroku config:set ENVIRONMENT=production
heroku config:set DEBUG=false

# Deploy
git push heroku main
```

---

### Option 4: DigitalOcean App Platform

#### Step 1: Prepare for DigitalOcean
Create a `do-app.yaml` file:

```yaml
name: drone-alert-system
services:
  - name: web
    source_dir: /
    github:
      repo: your-username/your-repo
      branch: main
    run_command: python main_production.py
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
      - key: MONGODB_URI
        value: mongodb+srv://your_username:your_password@your_cluster.mongodb.net/drone_alerts_db?retryWrites=true&w=majority
      - key: DATABASE_NAME
        value: drone_alerts_db
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: false
```

#### Step 2: Deploy
1. Go to [digitalocean.com](https://digitalocean.com)
2. Create App Platform
3. Connect your GitHub repository
4. Configure environment variables
5. Deploy

---

## 🔧 Environment Variables

Set these environment variables in your deployment platform:

```bash
# Required
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/drone_alerts_db?retryWrites=true&w=majority
DATABASE_NAME=drone_alerts_db

# Optional (with defaults)
ENVIRONMENT=production
DEBUG=false
PORT=8000
HOST=0.0.0.0
SECRET_KEY=your-secret-key-here
```

## 🗄️ MongoDB Atlas Setup (Free Cloud Database)

### Step 1: Create MongoDB Atlas Account
1. Go to [mongodb.com/atlas](https://mongodb.com/atlas)
2. Sign up for a free account
3. Create a new project

### Step 2: Create Cluster
1. Click "Build a Database"
2. Choose "FREE" tier (M0)
3. Select your preferred cloud provider and region
4. Click "Create"

### Step 3: Set Up Database Access
1. Go to "Database Access" → "Add New Database User"
2. Create a username and password
3. Select "Read and write to any database"
4. Click "Add User"

### Step 4: Set Up Network Access
1. Go to "Network Access" → "Add IP Address"
2. Click "Allow Access from Anywhere" (0.0.0.0/0)
3. Click "Confirm"

### Step 5: Get Connection String
1. Go to "Database" → "Connect"
2. Choose "Connect your application"
3. Copy the connection string
4. Replace `<password>` with your actual password
5. Add this to your deployment environment variables

## 🌍 Testing Your Deployed API

Once deployed, test your API:

### Health Check
```bash
curl https://your-app-url.railway.app/health
```

### Get Alerts
```bash
curl https://your-app-url.railway.app/api/alerts
```

### Create Alert
```bash
curl -X POST https://your-app-url.railway.app/api/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "intrusion",
    "score": 0.85,
    "location": {"lat": 40.7128, "lng": -74.0060},
    "drone_id": "test_drone_001"
  }'
```

### WebSocket Connection
```javascript
// Connect to WebSocket
const ws = new WebSocket('wss://your-app-url.railway.app/ws/drone/drone_001');

// Send alert
ws.send(JSON.stringify({
  "type": "alert",
  "data": {
    "alert_type": "intrusion",
    "score": 0.85,
    "location": {"lat": 40.7128, "lng": -74.0060},
    "drone_id": "drone_001"
  }
}));
```

## 📱 Using Your Deployed API

### Update Client Applications
Update your client applications to use the new URL:

```python
# Python client
SERVER_URL = "https://your-app-url.railway.app"
WEBSOCKET_URL = "wss://your-app-url.railway.app"
```

```javascript
// JavaScript client
const API_URL = "https://your-app-url.railway.app";
const WS_URL = "wss://your-app-url.railway.app";
```

### Dashboard Access
Your dashboard will be available at:
```
https://your-app-url.railway.app/dashboard/
```

## 🔒 Security Considerations

### For Production Use:
1. **Set up proper CORS** - Limit allowed origins
2. **Add authentication** - Implement API keys or JWT tokens
3. **Use HTTPS** - All major platforms provide this automatically
4. **Rate limiting** - Add rate limiting to prevent abuse
5. **Input validation** - Validate all incoming data
6. **Secure MongoDB** - Use strong passwords and network restrictions

### Environment Variables for Security:
```bash
# Add these for production
SECRET_KEY=your-very-secure-secret-key
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

## 🚨 Troubleshooting

### Common Issues:

1. **MongoDB Connection Error**
   - Check your connection string
   - Ensure IP whitelist includes 0.0.0.0/0
   - Verify username/password

2. **Port Issues**
   - Most platforms use `PORT` environment variable
   - Set `HOST=0.0.0.0` for external access

3. **WebSocket Issues**
   - Ensure platform supports WebSockets
   - Use `wss://` for secure WebSocket connections

4. **Build Failures**
   - Check `requirements.txt` is up to date
   - Verify Python version compatibility

### Getting Help:
- Check platform logs for error messages
- Test locally first with production settings
- Use the health endpoint to verify connectivity

## 🎉 Success!

Once deployed, your drone alert management system will be accessible from anywhere on the internet! 

**Your API endpoints will be:**
- 🌐 Main API: `https://your-app-url.railway.app`
- 📊 Dashboard: `https://your-app-url.railway.app/dashboard/`
- 📚 API Docs: `https://your-app-url.railway.app/docs`
- 🏥 Health: `https://your-app-url.railway.app/health`
- 📡 WebSocket: `wss://your-app-url.railway.app/ws/drone/{drone_id}` 