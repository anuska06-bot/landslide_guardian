# Rollback & Recovery Procedures

This document details the recovery mechanisms, rollback capabilities, and database considerations verified for the Landslide Guardian deployment.

---

## 1. Current Rollback Capabilities

| Component | Rollback Mechanism | Automation Level | Recovery Time |
| :--- | :--- | :--- | :--- |
| **Frontend (Vercel)** | Instant Instant Rollback via Vercel Dashboard | One-click manual action in Vercel UI | Under 30 seconds |
| **Backend (Railway)** | Redeploy Previous Deployment via Railway Dashboard | One-click manual action in Railway UI | 1 to 2 minutes |
| **Source Code (Git)** | `git revert` or branch reset to previous commit tag | Manual command via CLI | Immediate upon push |
| **Database Schemas** | *[NOT IMPLEMENTED]* | Manual script / manual DB surgery | Variable |

---

## 2. Platform-Specific Recovery Workflows

### 2.1 Frontend Rollback (Vercel)
Vercel preserves immutable snapshots for every build:
1. Log in to the [Vercel Dashboard](https://vercel.com).
2. Select the `landslide_guardian` project and navigate to the **Deployments** tab.
3. Locate the last known good deployment (prior to the problematic release).
4. Click the three dots (`...`) icon on the target deployment and select **Rollback to this deployment** (or **Promote to Production**).
5. Vercel instantly routes edge traffic to the selected deployment without rebuilding assets.

### 2.2 Backend Rollback (Railway)
Railway maintains build and deployment logs for previous runs:
1. Log in to the [Railway Dashboard](https://railway.app).
2. Select the Landslide Guardian project and choose the backend service.
3. Navigate to the **Deployments** tab.
4. Locate the last successfully running deployment.
5. Click **Redeploy** on that deployment card.
6. Railway will launch the previous container image and switch traffic to it once the startup command succeeds.

### 2.3 Git-Level Rollback
If a faulty commit was merged and pushed to `main`:
```bash
# Option A: Create a revert commit (recommended for collaborative branches)
git revert HEAD --no-edit
git push origin main

# Option B: Hard reset to a verified commit tag or SHA (requires force push)
# WARNING: Only use if authorized and coordinated with team members
git reset --hard <LAST_KNOWN_GOOD_COMMIT_HASH>
git push origin main --force
```

---

## 3. Database Migration & Data Integrity Considerations

### What is IMPLEMENTED:
- **Index Re-creation**: On server boot, `backend/database/mongodb.py` calls `_create_indexes()`, idempotently ensuring all required indexes exist across the 13 collections (`risk_assessments`, `alerts`, `citizens`, `incident_reports`, `sensor_readings`, `notification_log`, `rainfall_records`, `otps`, `offline_sos_queue`).
- **Graceful Missing Attribute Handling**: Application schemas use Pydantic `Optional` fields and dictionary `.get()` calls with sensible defaults, allowing older documents to be read without crashing new code.

### What is NOT IMPLEMENTED:
- **No Migration Framework**: There is no database migration manager (e.g., Alembic, Mongock, or migrate-mongo).
- **No Automated Down-Migrations**: If a new release writes fields or documents with altered semantics, rolling back code will not automatically undo or restructure existing MongoDB records.
- **No Database Snapshots on Release**: Automated database backups prior to production deployments are not configured in code or CI pipelines; backups rely entirely on manual MongoDB Atlas cloud snapshots.

---

## 4. Configuration Rollback

- Environment variables in Railway are updated immediately upon submission in the dashboard.
- Railway does not maintain a versioned history of environment variables.
- **Recovery Requirement**: If an environment variable change breaks the service (e.g. invalid `MONGODB_URI` or corrupted `ADMIN_SECRET`), the operator must manually re-enter the previous value in the Railway dashboard and trigger a redeployment.

---

## 5. Deployment Failure Recovery & Auto-Healing

### Railway Auto-Restart Policy
Defined in `railway.json`:
```json
"deploy": {
  "restartPolicyType": "ON_FAILURE",
  "restartPolicyMaxRetries": 10
}
```
- If the application process exits with a non-zero code during runtime, Railway automatically attempts up to 10 restarts before marking the deployment crashed.
- During a zero-downtime deployment, if the new build fails health checks on boot, Railway keeps the preceding container running, preventing user-facing downtime.

### Fallback to In-Memory Mode
- If MongoDB becomes unreachable during startup, the application does not crash-loop; it activates `MemoryDatabase`.
- **Caution**: While this prevents a total application outage, data saved during this period is volatile and will not persist across container restarts. Check `/api/health` immediately after recovery to verify database connectivity.
