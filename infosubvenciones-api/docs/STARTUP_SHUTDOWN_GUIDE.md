# InfoSubvenciones - System Startup & Shutdown Guide

Complete guide for starting, restarting, and shutting down the InfoSubvenciones API backend and frontend.

## Table of Contents
- [System Overview](#system-overview)
- [Prerequisites](#prerequisites)
- [Backend (Ingestion Pipeline)](#backend-ingestion-pipeline)
  - [Starting the Backend](#starting-the-backend)
  - [Restarting the Backend](#restarting-the-backend)
  - [Stopping the Backend](#stopping-the-backend)
- [Frontend (React Interface)](#frontend-react-interface)
  - [Starting the Frontend](#starting-the-frontend)
  - [Restarting the Frontend](#restarting-the-frontend)
  - [Stopping the Frontend](#stopping-the-frontend)
- [Quick Reference Commands](#quick-reference-commands)
- [Troubleshooting](#troubleshooting)

---

## System Overview

The InfoSubvenciones system consists of two main components:

### Backend Components:
1. **PostgreSQL Database** (Supabase) - Data storage
2. **Redis** - Message broker for Celery
3. **Celery Worker** - Asynchronous task processing
4. **Python Scripts** - Direct ingestion scripts (optional)

### Frontend Components:
1. **React + Vite Development Server** - Chat interface
2. **n8n Webhook** (external dependency) - Backend agent endpoint

---

## Prerequisites

Before starting, ensure you have:

### For Backend:
- ✅ Python 3.11+ installed
- ✅ Virtual environment activated
- ✅ PostgreSQL database accessible (Supabase)
- ✅ Redis server running (Docker or local)
- ✅ Environment variables configured in `Ingestion/.env`

### For Frontend:
- ✅ Node.js 18+ installed
- ✅ npm installed
- ✅ Environment variables configured in `interface/.env.local`

---

## Backend (Ingestion Pipeline)

The backend consists of Redis and Celery workers that process grant data.

### Starting the Backend

#### Step 1: Navigate to Project Root
```bash
cd "D:\IT workspace\infosubvenciones-api"
```

#### Step 2: Activate Python Virtual Environment
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux (if applicable)
source .venv/bin/activate
```

#### Step 3: Start Redis Server

**Option A: Using Docker (Recommended)**
```bash
# Start Redis container
docker run -d \
  --name infosubvenciones-redis \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:7-alpine

# Verify Redis is running
docker ps | grep infosubvenciones-redis
```

**Option B: Using Local Redis Installation**
```bash
# Windows (if installed as service)
net start Redis

# macOS/Linux
sudo systemctl start redis-server
# or
redis-server --daemonize yes
```

**Verify Redis Connection:**
```bash
redis-cli ping
# Expected output: PONG
```

#### Step 4: Start Celery Worker

Open a **new terminal window** and run:

```bash
# Navigate to project root
cd "D:\IT workspace\infosubvenciones-api"

# Activate virtual environment
.venv\Scripts\activate

# Start Celery worker for fetcher queue
celery -A Ingestion.config.celery_app worker --loglevel=info -Q fetcher

# Keep this terminal open - this is your worker process
```

**Expected Output:**
```
 -------------- celery@YOUR-COMPUTER v5.3.x (singularity)
--- ***** -----
-- ******* ---- Windows-10.x.x
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         celery_app:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
...
[INFO] Ready to process tasks on queue: fetcher
```

#### Step 5: (Optional) Start Additional Workers for Processing

If you need to run PDF processing or embedding tasks, start additional workers:

**Terminal 2 - Processor Worker:**
```bash
cd "D:\IT workspace\infosubvenciones-api"
.venv\Scripts\activate
celery -A Ingestion.config.celery_app worker --loglevel=info -Q processor --concurrency=4
```

**Terminal 3 - Embedder Worker:**
```bash
cd "D:\IT workspace\infosubvenciones-api"
.venv\Scripts\activate
celery -A Ingestion.config.celery_app worker --loglevel=info -Q embedder --concurrency=2
```

#### Step 6: Test the Backend

In a **new terminal**, run a quick test:

```bash
cd "D:\IT workspace\infosubvenciones-api"
.venv\Scripts\activate
python Ingestion/scripts/test_pipeline.py --items 5 --direct
```

**Success indicators:**
- ✅ Test completes without errors
- ✅ Celery worker logs show task execution
- ✅ Redis connection stable
- ✅ Database records inserted

---

### Restarting the Backend

To restart the backend (e.g., after code changes or configuration updates):

#### Quick Restart (Celery Workers Only)

1. **Stop Celery Workers:**
   - In each Celery terminal window, press `Ctrl+C`
   - Wait for "Worker shutdown" message

2. **Restart Workers:**
   ```bash
   # In each worker terminal
   celery -A Ingestion.config.celery_app worker --loglevel=info -Q fetcher
   # (Repeat for processor, embedder as needed)
   ```

#### Full Restart (All Services)

1. **Stop All Services** (see [Stopping the Backend](#stopping-the-backend))
2. **Clear Redis Cache (Optional):**
   ```bash
   redis-cli FLUSHDB
   ```
3. **Restart All Services** (follow [Starting the Backend](#starting-the-backend))

#### Restart After Code Changes

**For Python code changes:**
```bash
# In Celery worker terminal(s):
# 1. Press Ctrl+C to stop worker
# 2. Restart worker
celery -A Ingestion.config.celery_app worker --loglevel=info -Q fetcher
```

**For configuration changes (`.env` file):**
```bash
# Stop all workers (Ctrl+C in each terminal)
# Restart each worker - new environment variables will be loaded
```

---

### Stopping the Backend

#### Step 1: Stop Celery Workers

In each Celery worker terminal:
```bash
# Press Ctrl+C
# Wait for graceful shutdown message:
# "Warm shutdown (MainProcess)"
```

If workers don't stop gracefully (after 30 seconds):
```bash
# Force kill (Windows)
taskkill /F /IM celery.exe

# Force kill (macOS/Linux)
pkill -9 celery
```

#### Step 2: Stop Redis

**If using Docker:**
```bash
# Stop Redis container
docker stop infosubvenciones-redis

# (Optional) Remove container
docker rm infosubvenciones-redis
```

**If using local Redis:**
```bash
# Windows
net stop Redis

# macOS/Linux
sudo systemctl stop redis-server
# or
redis-cli shutdown
```

#### Step 3: Deactivate Virtual Environment

```bash
deactivate
```

#### Verification

Confirm all services stopped:
```bash
# Check Redis
redis-cli ping
# Expected: Connection refused

# Check Celery processes (Windows)
tasklist | findstr celery
# Expected: No output

# Check Celery processes (macOS/Linux)
ps aux | grep celery
# Expected: Only the grep command itself
```

---

## Frontend (React Interface)

The frontend is a React + Vite chat interface.

### Starting the Frontend

#### Step 1: Navigate to Interface Directory
```bash
cd "D:\IT workspace\interface"
```

#### Step 2: Install Dependencies (First Time Only)

If you haven't already installed node modules:
```bash
npm install
```

**Expected output:**
```
added 250 packages in 15s
```

#### Step 3: Configure Environment Variables

Ensure `.env.local` exists with proper configuration:

```bash
# Create .env.local from example (if not exists)
cp .env.example .env.local

# Edit .env.local with required values:
# VITE_AGENT_ENDPOINT=<your-n8n-webhook-url>
# VITE_AGENT_BASIC_AUTH_USER=<username>
# VITE_AGENT_BASIC_AUTH_PASS=<password>
# VITE_AGENT_TIMEOUT_MS=30000
# VITE_APP_LAST_UPDATED=2025-12-09
```

#### Step 4: Start Development Server

```bash
npm run dev
```

**Expected Output:**
```
  VITE v5.4.10  ready in 450 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

#### Step 5: Access the Interface

Open your browser and navigate to:
```
http://localhost:5173/
```

**Success indicators:**
- ✅ Page loads without errors
- ✅ Chat interface is visible
- ✅ Filter options render correctly
- ✅ No console errors in browser DevTools (F12)

---

### Restarting the Frontend

#### Quick Restart (Development Server Only)

1. **Stop the server:**
   - In the terminal running Vite, press `Ctrl+C`

2. **Start the server again:**
   ```bash
   npm run dev
   ```

#### Restart After Changes

**For code changes (.tsx, .ts files):**
- Vite has **Hot Module Replacement (HMR)** - most changes auto-reload
- No restart needed in most cases

**For configuration changes (.env.local):**
```bash
# Stop server (Ctrl+C)
# Restart server
npm run dev
```

**For dependency changes (package.json):**
```bash
# Stop server (Ctrl+C)
# Reinstall dependencies
npm install
# Restart server
npm run dev
```

#### Clear Build Cache (If Needed)

```bash
# Stop server (Ctrl+C)
# Remove node modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev

# Windows alternative for rm -rf
rmdir /s /q node_modules
del package-lock.json
npm install
npm run dev
```

---

### Stopping the Frontend

#### Step 1: Stop Development Server

In the terminal running Vite:
```bash
# Press Ctrl+C
```

**Expected output:**
```
Server closed
```

#### Verification

```bash
# Try accessing the URL
curl http://localhost:5173/
# Expected: Connection refused or timeout
```

---

## Quick Reference Commands

### Backend Startup (Complete Sequence)

```bash
# Terminal 1: Redis
docker run -d --name infosubvenciones-redis -p 6379:6379 redis:7-alpine

# Terminal 2: Celery Worker
cd "D:\IT workspace\infosubvenciones-api"
.venv\Scripts\activate
celery -A Ingestion.config.celery_app worker --loglevel=info -Q fetcher
```

### Backend Shutdown

```bash
# Ctrl+C in Celery terminals
docker stop infosubvenciones-redis
deactivate
```

### Frontend Startup

```bash
cd "D:\IT workspace\interface"
npm run dev
```

### Frontend Shutdown

```bash
# Ctrl+C in Vite terminal
```

---

## Troubleshooting

### Backend Issues

#### Problem: "Cannot connect to Redis"
**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not, start Redis
docker run -d --name infosubvenciones-redis -p 6379:6379 redis:7-alpine

# Check if port is already in use
netstat -ano | findstr :6379
```

#### Problem: "Database connection failed"
**Solution:**
```bash
# Verify DATABASE_URL in Ingestion/.env
# Test database connection
python -c "from Ingestion.config.database import engine; print(engine.connect())"

# Check Supabase database status at:
# https://supabase.com/dashboard/project/vtbvcabetythqrdedgee
```

#### Problem: "Module not found" errors
**Solution:**
```bash
# Ensure virtual environment is activated
.venv\Scripts\activate

# Reinstall dependencies
pip install -r Ingestion/requirements.txt
```

#### Problem: Celery worker stuck or frozen
**Solution:**
```bash
# Force kill all Celery processes
taskkill /F /IM celery.exe  # Windows
pkill -9 celery             # macOS/Linux

# Clear Redis queue
redis-cli FLUSHDB

# Restart worker
celery -A Ingestion.config.celery_app worker --loglevel=info -Q fetcher
```

#### Problem: "No module named 'Ingestion'"
**Solution:**
```bash
# Ensure you're running from project root
cd "D:\IT workspace\infosubvenciones-api"

# Add project root to PYTHONPATH (Windows)
set PYTHONPATH=%PYTHONPATH%;D:\IT workspace\infosubvenciones-api

# macOS/Linux
export PYTHONPATH=$PYTHONPATH:/path/to/infosubvenciones-api
```

### Frontend Issues

#### Problem: "Port 5173 already in use"
**Solution:**
```bash
# Find process using port 5173
netstat -ano | findstr :5173

# Kill the process (Windows)
taskkill /F /PID <PID>

# Or use a different port
npm run dev -- --port 3000
```

#### Problem: "Cannot connect to backend API"
**Solution:**
```bash
# Verify VITE_AGENT_ENDPOINT in .env.local
# Test endpoint manually
curl -X POST <VITE_AGENT_ENDPOINT> -H "Content-Type: application/json" -d '{"test": "data"}'

# Check browser console (F12) for CORS errors
# Ensure n8n webhook allows your frontend origin
```

#### Problem: Blank page or white screen
**Solution:**
```bash
# Check browser console (F12) for errors
# Clear browser cache (Ctrl+Shift+Delete)
# Rebuild frontend
npm run build
npm run preview

# If still failing, reinstall
rm -rf node_modules
npm install
npm run dev
```

#### Problem: Environment variables not loading
**Solution:**
```bash
# Verify .env.local exists (not .env.example)
ls .env.local

# Ensure variables start with VITE_
# Restart dev server after .env.local changes
```

### Common Issues (Both)

#### Problem: Changes not reflecting
**Backend:**
```bash
# Restart Celery worker (Ctrl+C, then restart)
```

**Frontend:**
```bash
# Hard refresh browser (Ctrl+Shift+R)
# Or restart dev server
```

#### Problem: "Permission denied" errors (Windows)
**Solution:**
```bash
# Run terminal as Administrator
# Right-click Terminal/PowerShell → "Run as Administrator"
```

#### Problem: Python/Node version mismatch
**Solution:**
```bash
# Check versions
python --version  # Should be 3.11+
node --version    # Should be 18+

# Update if needed using official installers
```

---

## Production Deployment Notes

For production deployment (not covered in detail here):

### Backend:
- Use **supervisord** or **systemd** to manage Celery workers
- Configure Redis persistence with `appendonly yes`
- Set up log rotation for Celery logs
- Use environment-specific `.env` files
- Monitor with Flower: `celery -A Ingestion.config.celery_app flower`

### Frontend:
- Build for production: `npm run build`
- Serve with nginx or similar: `npm run preview` (testing only)
- Configure proper CORS headers on n8n webhook
- Set up SSL/TLS certificates
- Use environment-specific `.env.production` file

---

## Additional Resources

- **Backend Documentation**: [Ingestion/README.md](../Ingestion/README.md)
- **Ingestion Strategy**: [docs/Ingestion_strategy.md](Ingestion_strategy.md)
- **Frontend Documentation**: [interface/README.md](../../interface/README.md)
- **Celery Documentation**: https://docs.celeryq.dev/
- **Vite Documentation**: https://vitejs.dev/

---

**Last Updated**: 2025-12-09
**Maintained By**: InfoSubvenciones Development Team
