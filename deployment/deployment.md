# Deployment Architecture & Operations

This document outlines the verified deployment architecture, hosting infrastructure, live routing mechanisms, and operational verification procedures for Landslide Guardian.

---

## 1. Actual Deployment Architecture

Landslide Guardian operates on a decoupled multi-cloud architecture:

```
                      +------------------------------------------+
                      |         End User / Web Browser          |
                      +------------------------------------------+
                                    |              |
           Static Assets            |              | Direct API Calls
     (HTML, CSS, JS, Images)        |              | (via frontend/api.js)
                                    v              v
               +-------------------------+   +------------------------------------+
               |      Vercel Edge        |   |           Railway Service          |
               | (Frontend Hosting)      |   |          (FastAPI Backend)         |
               |                         |   |                                    |
               | Rewrites:               |   | Base URL:                          |
               | /api/* -----(Proxy)---->|-->| https://landslideguardian-         |
               | /uploads/* -(Proxy)---->|-->|  production.up.railway.app         |
               |                         |   |                                    |
               | Static files:           |   | - Lifespan: background_monitor_loop|
               | /frontend/*             |   | - ML Engine: ExtraTreesClassifier  |
               +-------------------------+   +------------------------------------+
                                                               |
                                        +----------------------+----------------------+
                                        |                      |                      |
                                        v                      v                      v
                             +--------------------+ +--------------------+ +--------------------+
                             |   MongoDB Atlas    | |     Open-Meteo     | |   Brevo / Resend   |
                             |  (Cloud Database)  | |  (Live Weather)    | |  (Transactional    |
                             |  DB: landslide_    | |  api.open-meteo.   | |   Email Alerts)    |
                             |      guardian      | |       com          | |                    |
                             +--------------------+ +--------------------+ +--------------------+
```

### Components:
1. **Frontend (Vercel)**:
   - Hosts static web assets from `frontend/`.
   - Proxies `/api/*` and `/uploads/*` requests to the Railway backend via rules in `vercel.json`.
   - Client-side code in `frontend/api.js` also contains direct routing fallbacks pointing to `https://landslideguardian-production.up.railway.app/api`.
2. **Backend (Railway)**:
   - Hosts the Python FastAPI server managed by Uvicorn.
   - Built automatically via Nixpacks (`railway.json`).
   - Runs continuous background worker thread `background_monitor_loop` every 15 minutes to recompute risk for all 8 Northeast states.
3. **Database (MongoDB Atlas)**:
   - Cloud MongoDB instance storing registered citizens, incident reports, alerts, OTP digests, and offline SOS queues.
   - Fallback: If unreachable, switches to ephemeral in-memory storage (`MemoryDatabase`).
4. **Third-Party Telemetry & Messaging**:
   - Open-Meteo for live precipitation, soil moisture, and weather forecasts.
   - Brevo HTTP API (primary) -> Resend HTTP API (secondary) -> Direct SMTP (fallback) for zero-failure alerts.

---

## 2. Deployment Prerequisites

- **GitHub Repository**: Code pushed to `main` branch (`https://github.com/anuska06-bot/landslide_guardian.git`).
- **Railway Account**:
  - Connected to GitHub repository.
  - Project created with one active Service pointing to repository root.
- **Vercel Account**:
  - Connected to GitHub repository.
  - Root directory set to project root (reads `vercel.json`).
- **MongoDB Atlas Cluster**:
  - Network Access: Allow access from anywhere (`0.0.0.0/0`) or Railway static egress IP.
  - Database user with read/write privileges on database `landslide_guardian`.

---

## 3. Exact Verified Deployment Steps

### Backend Deployment (Railway)
1. **Push Changes**:
   Ensure all changes are committed and pushed to `main` on GitHub:
   ```bash
   git push origin main
   ```
2. **Configure Railway Environment Variables**:
   In Railway Dashboard -> Project -> Service -> **Variables**, inject:
   - `MONGODB_URI`: `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/landslide_guardian?retryWrites=true&w=majority`
   - `ADMIN_USERNAME`: Desired administrative username.
   - `ADMIN_PASSWORD`: Strong administrative password.
   - `ADMIN_SECRET`: Cryptographic token signing secret.
   - `BREVO_API_KEY`: Brevo transactional API key.
   - `ALERT_FROM_EMAIL`: Authorized sender address.
   - `MONITOR_INTERVAL_MINUTES`: `15`
   - `SOS_COOLDOWN_MINUTES`: `60`
   - `OTP_SALT`: Unique salt string for OTP hashing.
3. **Automatic Build & Start**:
   Railway triggers a Nixpacks build upon detecting the GitHub push.
   It executes the start command defined in `railway.json`:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```
4. **Railway Public Domain**:
   Verify or assign the public domain under Service Settings -> Networking -> Public Networking:
   `landslideguardian-production.up.railway.app`.

### Frontend Deployment (Vercel)
1. **Connect Repository**:
   Import `landslide_guardian` in Vercel Dashboard.
2. **Framework Preset**:
   Select **Other** (no build command, output directory empty / root).
3. **Build & Output Settings**:
   - Build Command: Leave blank (no npm build).
   - Output Directory: Leave blank.
4. **Deploy**:
   Vercel reads `vercel.json` from the repository root:
   - Maps static requests to `/frontend/`.
   - Directs `/api/:path*` to `https://landslideguardian-production.up.railway.app/api/:path*`.
   - Injects `no-cache` response headers.

---

## 4. Health Checks & Verification Steps

After deployment, perform the following verification sequence:

### Step 1: Backend System Health Endpoint
Request:
```bash
curl -s https://landslideguardian-production.up.railway.app/api/health
```
Expected Response:
```json
{
  "status": "healthy",
  "api_version": "3.0.0",
  "database_connected": true,
  "system": "Landslide Guardian API",
  "mode": "Software-only live weather + ML + future sensor interface"
}
```
*Note: Verify that `"database_connected"` is `true`. If `false`, MongoDB Atlas connectivity failed.*

### Step 2: System Configuration Endpoint
Request:
```bash
curl -s https://landslideguardian-production.up.railway.app/api/config
```
Expected Response:
```json
{
  "api_version": "3.0.0",
  "build_version": "3.0.0",
  "storage_mode": "mongodb_atlas",
  "automatic_monitoring": true,
  "regions": 8,
  "smtp_configured": true
}
```

### Step 3: Frontend-to-Backend Rewrite Proxy
Request:
```bash
curl -s https://landslideguardian.vercel.app/api/health
```
Verify that the response returns the same JSON payload as the Railway backend, confirming the Vercel proxy rewrite is functioning correctly.

---

## 5. Common Deployment Failure Points Discovered

1. **IPv6 SMTP Failure in Cloud Containers**:
   - *Issue*: Cloud hosting environments (such as Railway or Render) often fail when attempting outbound SMTP connections over IPv6, throwing `[Errno 101] Network is unreachable`.
   - *Mitigation in Project*: `backend/services/notification_service.py` provides custom `IPv4SMTP` and `IPv4SMTP_SSL` classes, and prioritizes HTTP-based email APIs (Brevo and Resend) over raw SMTP.
2. **Ephemeral Uploads Storage**:
   - *Issue*: Crowdsourced incident report photos uploaded via `/api/reports/submit` are written to local disk at `backend/uploads/`.
   - *Risk*: Without a persistent volume mount in Railway, files in `backend/uploads/` are erased whenever the container restarts or redeploys.
3. **Silent Database Degradation**:
   - *Issue*: `backend/database/mongodb.py` catches all MongoDB connection errors and silently falls back to `MemoryDatabase`.
   - *Risk*: If `MONGODB_URI` has bad credentials or IP whitelisting issues, the app boots successfully without throwing an error, but all user registrations and reports exist only in RAM and vanish upon container restart. Inspect `/api/health` to detect this state.
4. **Vercel Serverless Background Task Freeze**:
   - *Issue*: Serverless platforms freeze execution after HTTP responses finish.
   - *Safeguard in Project*: `backend/main.py` explicitly skips scheduling `background_monitor_loop` if `os.getenv("VERCEL")` is present. Background monitoring runs exclusively on Railway.
