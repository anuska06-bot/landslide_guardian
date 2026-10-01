# Production Release Checklist

This checklist must be executed before deploying updates to the Landslide Guardian production environments (Railway backend + Vercel frontend).

---

## Phase 1: Pre-Release Code & Build Validation

- [ ] **Working Tree Cleanliness**: Confirm all local edits are committed and untracked files are accounted for (`git status`).
- [ ] **Dependencies Audited**: If new Python libraries were introduced, ensure they are mirrored across both `requirements.txt` and `backend/requirements.txt`.
- [ ] **Model Artifact Status**: If `backend/ml/train_model.py` or `real_landslide_50k_dataset.csv` was updated, confirm `backend/ml/model.pkl` was retrained and verified.
- [ ] **Static Code Inspection**: Ensure no temporary debug prints, breakpoint statements (`pdb`), or hardcoded credentials exist in source files.
- [ ] **Static Asset Verification**: Confirm all referenced frontend icons, images, and stylesheets exist in `frontend/assets/` or `frontend/css/`.

---

## Phase 2: Automated Testing & Integrity Checks

- [ ] **Test Discovery Run**: Execute the full test suite from the repository root:
  ```bash
  python -m unittest discover -s backend -t . -p "test_*.py"
  ```
- [ ] **Compliance Test Verification**: Confirm `TestSIHCompliance` reports 10/10 tests passing (ML inference, Factor of Safety physics, pore pressure calculations, multilingual alerts, corridor routes).
- [ ] **Regional Test Verification**: Confirm `TestRegionalLandslideSystem` reports 5/5 tests passing (all 8 NER states present, location lookups, grid bounds).
- [ ] **Database Connection Test**: Execute `python backend/test_mongodb.py` to confirm remote Atlas connectivity if testing with live credentials.

---

## Phase 3: Environment Configuration & Secrets

- [ ] **`ADMIN_SECRET`**: Confirm a high-entropy secret is configured in Railway (do NOT rely on `"change-this-sih-secret"`).
- [ ] **`ADMIN_PASSWORD`**: Confirm a secure administrative password is set (do NOT rely on `"guardian-demo"`).
- [ ] **`MONGODB_URI`**: Confirm the connection string points to the production cluster with read-write permissions and verified IP whitelist access.
- [ ] **Email Provider Keys**:
  - If using Brevo: Confirm `BREVO_API_KEY` and `ALERT_FROM_EMAIL` are valid.
  - If using Resend: Confirm `RESEND_API_KEY` is active.
  - If using SMTP: Confirm `SMTP_HOST`, `SMTP_PORT` (465 SSL recommended), `SMTP_USER`, and `SMTP_PASSWORD` are valid.
- [ ] **Monitoring Timing**: Verify `MONITOR_INTERVAL_MINUTES=15` and `SOS_COOLDOWN_MINUTES=60` in the environment.

---

## Phase 4: Compatibility & Routing Verification

- [ ] **Frontend-to-Backend Rewrite Compatibility**:
  - In `frontend/api.js`: Verify `RAILWAY_BACKEND_ORIGIN` matches the active Railway domain (`https://landslideguardian-production.up.railway.app`).
  - In `vercel.json`: Verify destination URLs in rewrites match the Railway backend URL.
- [ ] **API Endpoint Backward Compatibility**:
  - Ensure updated endpoints do not remove existing fields expected by `frontend/api.js` (`/api/locations`, `/api/risk/evaluate`, `/api/alerts/active`, `/api/health`, `/api/config`).
- [ ] **CORS Configuration**: Verify `allow_origins` in `backend/main.py` permits requests from the Vercel domain.

---

## Phase 5: Deployment Execution

- [ ] **Push to Remote**: Push commits to the `main` branch of `origin`:
  ```bash
  git push origin main
  ```
- [ ] **Railway Deployment Monitoring**:
  - Open the Railway dashboard.
  - Watch the build log: confirm Nixpacks successfully installed Python packages.
  - Watch the deploy log: confirm Uvicorn started on `0.0.0.0:${PORT}` and logged `"Automatic monitoring loop scheduled."`.
- [ ] **Vercel Deployment Monitoring**:
  - Open the Vercel dashboard.
  - Confirm the latest deployment status displays as **Ready**.

---

## Phase 6: Post-Deployment Smoke Tests

- [ ] **Live Health Probe**:
  ```bash
  curl -s https://landslideguardian-production.up.railway.app/api/health
  ```
  Confirm `"status": "healthy"` and `"database_connected": true`.
- [ ] **Configuration Probe**:
  ```bash
  curl -s https://landslideguardian-production.up.railway.app/api/config
  ```
  Confirm `"storage_mode": "mongodb_atlas"`, `"regions": 8`, and `"automatic_monitoring": true`.
- [ ] **Vercel Reverse Proxy Verification**:
  ```bash
  curl -s https://landslideguardian.vercel.app/api/health
  ```
  Confirm the proxy successfully forwards the request and returns the exact same health JSON.
- [ ] **WebGIS Map Smoke Test**:
  - Open `https://landslideguardian.vercel.app/map.html`.
  - Confirm the base map tiles load, 8 state risk overlays render, and highway corridor polyline markers appear.
- [ ] **Citizen Registration & OTP Verification**:
  - Navigate to `https://landslideguardian.vercel.app/alerts.html`.
  - Register a test email and verify that OTP delivery succeeds.
- [ ] **Interactive Risk Assessment**:
  - Navigate to `https://landslideguardian.vercel.app/assessment.html`.
  - Select a location (e.g., Gangtok, Sikkim) and submit an evaluation. Confirm risk gauge and factor breakdown render correctly.
- [ ] **Admin Authentication**:
  - Access `https://landslideguardian.vercel.app/admin-login.html`.
  - Log in with production administrative credentials and verify session cookie/token generation.

---

## Phase 7: Rollback Preparedness

- [ ] **Previous Deployment Identified**: Confirm the previous deployment SHA and container ID in Railway are visible and marked ready for rollback if needed.
- [ ] **Emergency Contact**: Ensure key team members are reachable during the deployment window.
