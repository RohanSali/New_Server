# 🚨 Railway Deployment Troubleshooting

## Common Issues and Solutions

### Issue: "Service Unavailable" Health Check Failures

**Symptoms:**
- Railway shows "service unavailable" errors
- Health check at `/health` fails
- App doesn't start properly

**Solutions:**

#### 1. Check Environment Variables
Make sure these are set in Railway dashboard:

```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/drone_alerts_db?retryWrites=true&w=majority
DATABASE_NAME=drone_alerts_db
ENVIRONMENT=production
DEBUG=false
PORT=8000
HOST=0.0.0.0
```

#### 2. Check Railway Logs
1. Go to Railway dashboard
2. Click on your project
3. Go to "Deployments" tab
4. Click on the latest deployment
5. Check the logs for errors

#### 3. Common Log Errors and Fixes

**Error: "ModuleNotFoundError"**
```
ModuleNotFoundError: No module named 'fastapi'
```
**Fix:** Make sure `requirements.txt` is in the root directory

**Error: "MONGODB_URI not set"**
```
MONGODB_URI environment variable is not set!
```
**Fix:** Set MONGODB_URI in Railway environment variables

**Error: "Connection refused"**
```
Connection refused to MongoDB
```
**Fix:** Check MongoDB Atlas network access (allow 0.0.0.0/0)

**Error: "Port already in use"**
```
Address already in use
```
**Fix:** Railway handles this automatically, but check if PORT is set correctly

### Issue: App Starts but Health Check Fails

**Solution:** The health check endpoint is now more robust and should work even if database connection fails.

### Issue: Build Failures

**Check these files exist in your repository:**
- ✅ `requirements.txt`
- ✅ `Procfile`
- ✅ `railway.json`
- ✅ `start_railway.py`
- ✅ `main_production.py`

### Issue: MongoDB Connection Problems

#### 1. MongoDB Atlas Setup
1. Go to [mongodb.com/atlas](https://mongodb.com/atlas)
2. Create free account
3. Create cluster (free tier)
4. Set up database user
5. Set up network access (allow 0.0.0.0/0)
6. Get connection string

#### 2. Connection String Format
```
mongodb+srv://username:password@cluster.mongodb.net/drone_alerts_db?retryWrites=true&w=majority
```

**Important:** Replace `username`, `password`, and `cluster` with your actual values.

### Issue: App Deploys but WebSocket Doesn't Work

**Solution:** WebSocket connections use `wss://` (secure) instead of `ws://` in production.

### Issue: Dashboard Not Loading

**Solution:** The dashboard route has been fixed and should work at `/dashboard/`

## 🔧 Manual Railway Deployment Steps

### Step 1: Prepare Your Repository
```bash
# Make sure all files are committed
git add .
git commit -m "Fix Railway deployment"
git push origin main
```

### Step 2: Railway Setup
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository

### Step 3: Environment Variables
In Railway dashboard → Variables tab, add:

```bash
MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/drone_alerts_db?retryWrites=true&w=majority
DATABASE_NAME=drone_alerts_db
ENVIRONMENT=production
DEBUG=false
PORT=8000
HOST=0.0.0.0
```

### Step 4: Deploy
1. Railway will automatically detect the Python app
2. It will use `start_railway.py` as the entry point
3. Wait for deployment to complete
4. Check logs for any errors

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production",
  "database_connected": true,
  "websocket_stats": {"total_connections": 0},
  "timestamp": "2025-07-26T00:00:00Z"
}
```

### 2. Test API
```bash
curl https://your-app.railway.app/api/alerts
```

### 3. Test WebSocket
```javascript
const ws = new WebSocket('wss://your-app.railway.app/ws/drone/test');
ws.onopen = () => console.log('Connected!');
```

## 📞 Getting Help

### Check Railway Logs
1. Go to Railway dashboard
2. Click on your project
3. Go to "Deployments"
4. Click on deployment
5. Check "Logs" tab

### Common Log Messages
- ✅ "Starting Drone Alert Management System on Railway..." - App starting
- ✅ "Railway Environment Setup:" - Environment configured
- ✅ "Starting server on 0.0.0.0:8000" - Server started
- ❌ "MONGODB_URI environment variable is not set!" - Missing env var
- ❌ "Import error" - Missing dependencies

### Railway Support
- Check [Railway documentation](https://docs.railway.app)
- Join [Railway Discord](https://discord.gg/railway)
- Check [Railway status page](https://status.railway.app)

## 🎯 Quick Fix Checklist

- [ ] All files committed to GitHub
- [ ] `requirements.txt` exists and is correct
- [ ] `Procfile` exists and points to `start_railway.py`
- [ ] `railway.json` exists and is correct
- [ ] `MONGODB_URI` is set in Railway environment variables
- [ ] MongoDB Atlas is set up and accessible
- [ ] Network access allows 0.0.0.0/0 in MongoDB Atlas
- [ ] Railway deployment completed successfully
- [ ] Health check returns 200 OK
- [ ] API endpoints are accessible

## 🚀 Alternative: Use Render Instead

If Railway continues to have issues, try [Render](https://render.com):

1. Go to [render.com](https://render.com)
2. Connect your GitHub repository
3. Create new Web Service
4. Use `render.yaml` configuration
5. Set environment variables
6. Deploy

Render often has better Python support and fewer deployment issues. 