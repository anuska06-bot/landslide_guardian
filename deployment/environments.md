# Environment Specifications

This document outlines the verified environment configurations, runtime parameters, secrets management, and dependency footprints for the Landslide Guardian project.

---

## 1. Verified Environments Overview

The project exhibits two verified active runtime environments, with staging being unconfigured.

| Environment | Hosting Platform | Host URL / Binding | Database Engine | Primary Role |
| :--- | :--- | :--- | :--- | :--- |
| **Development (Local)** | Local Machine (Windows / POSIX) | `http://127.0.0.1:8000` or `http://localhost:8000` | In-Memory Database (`MemoryDatabase`) or local/remote MongoDB Atlas | Local development, unit test execution, model training |
| **Staging** | *[UNKNOWN / NOT CONFIGURED]* | *None* | *None* | No staging pipeline, staging URL, or preview database exists in the repository. |
| **Production (Backend)** | Railway | `https://landslideguardian-production.up.railway.app` | MongoDB Atlas (Cluster 0, DB: `landslide_guardian`) | REST API, ML inference, background monitoring, automated SOS dispatch |
| **Production (Frontend)** | Vercel | `https://landslideguardian.vercel.app` (configured via `vercel.json` rewrites) | None (Static HTML/JS client calling Railway API) | Public WebGIS portal, admin dashboard, citizen registration |

---

## 2. Environment Variables & Purpose

The backend checks for configuration in `backend/.env`, root `.env`, and OS process environment variables via `os.getenv()`.

### Core Application & Database
- `PORT`
  - **Purpose**: TCP port on which Uvicorn binds.
  - **Default**: `8000` locally. Set dynamically by cloud container orchestrators (Railway assigns `PORT`).
  - **Verified**: Yes (in `backend/main.py`, `Procfile`, `railway.json`).
- `MONGODB_URI`
  - **Purpose**: MongoDB Atlas SRV connection string (e.g. `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/landslide_guardian?retryWrites=true&w=majority`).
  - **Fallback**: If omitted or unreachable, `backend/database/mongodb.py` initializes an ephemeral in-memory database (`MemoryDatabase`).
  - **Verified**: Yes (in `backend/database/mongodb.py`).
- `VERCEL`
  - **Purpose**: Flag indicating execution in a serverless Vercel function runtime.
  - **Behavior**: If detected, disables the asynchronous background monitoring loop (`background_monitor_loop`) in `backend/main.py` lifespan to prevent process freeze in serverless execution.
  - **Verified**: Yes (in `backend/main.py`).

### Security & Administration
- `ADMIN_USERNAME`
  - **Purpose**: Administrative console login username.
  - **Default**: `"admin"`
  - **Verified**: Yes (in `backend/routes/admin.py`).
- `ADMIN_PASSWORD`
  - **Purpose**: Administrative console login password.
  - **Default**: `"guardian-demo"`
  - **Verified**: Yes (in `backend/routes/admin.py`).
- `ADMIN_SECRET`
  - **Purpose**: Secret key for cryptographic signing of administrative session tokens.
  - **Default**: `"change-this-sih-secret"`
  - **Verified**: Yes (in `backend/services/admin_auth.py`).

### Citizen Registration & OTP Verification
- `OTP_SALT`
  - **Purpose**: Salt string used for HMAC-SHA256 digestion of 6-digit citizen verification OTPs before persistence.
  - **Default**: `"landslide-guardian-otp-salt"`
  - **Verified**: Yes (in `backend/services/otp_service.py`).
- `OTP_EXPIRY_MINUTES`
  - **Purpose**: Lifetime of an issued verification OTP before expiration.
  - **Default**: `10`
  - **Verified**: Yes (in `backend/services/otp_service.py`).
- `OTP_RESEND_COOLDOWN_SECONDS`
  - **Purpose**: Minimum time required before a user can request an OTP resend.
  - **Default**: `60`
  - **Verified**: Yes (in `backend/services/otp_service.py`).
- `OTP_MAX_ATTEMPTS`
  - **Purpose**: Maximum incorrect attempts before an OTP is invalidated.
  - **Default**: `5`
  - **Verified**: Yes (in `backend/services/otp_service.py`).

### Autonomous Monitoring & Anti-Spam Cooldown
- `MONITOR_INTERVAL_MINUTES`
  - **Purpose**: Frequency at which `background_monitor_loop` scans all 8 NER states and recomputes risk.
  - **Default**: `15` (converted to 900 seconds in `backend/services/monitor.py`).
  - **Verified**: Yes.
- `SOS_COOLDOWN_MINUTES`
  - **Purpose**: Minimum cooldown period between automated regional alerts dispatched to the same region.
  - **Default**: `60` (converted to 3600 seconds in `backend/services/monitor.py`). Can be bypassed on severe risk surges.
  - **Verified**: Yes.

### Emergency Alert Notification Providers (Failover Pipeline)
- `BREVO_API_KEY`
  - **Purpose**: API key for Brevo transactional email HTTP API (`https://api.brevo.com/v3/smtp/email`). Primary provider.
  - **Fallback**: If absent or failing, attempts Resend HTTP API.
  - **Verified**: Yes (in `backend/services/notification_service.py`).
- `RESEND_API_KEY`
  - **Purpose**: API key for Resend transactional email HTTP API (`https://api.resend.com/emails`). Secondary provider.
  - **Fallback**: If absent or failing, attempts direct SMTP.
  - **Verified**: Yes (in `backend/services/notification_service.py`).
- `SMTP_HOST` / `SMTP_SERVER`
  - **Purpose**: Mail server host for direct SMTP delivery (e.g. `smtp.gmail.com`).
  - **Verified**: Yes.
- `SMTP_PORT`
  - **Purpose**: Port for direct SMTP delivery. Defaults to `465` (SSL) for cloud environments, falls back to `587` (STARTTLS).
  - **Verified**: Yes.
- `SMTP_USER` / `SMTP_EMAIL` / `EMAIL_USERNAME`
  - **Purpose**: SMTP username / email address.
  - **Verified**: Yes.
- `SMTP_PASSWORD` / `EMAIL_PASSWORD`
  - **Purpose**: SMTP password or Gmail App Password.
  - **Verified**: Yes.
- `ALERT_FROM_EMAIL` / `EMAIL_FROM`
  - **Purpose**: Envelope and header `From:` sender address. Defaults to `SMTP_USER` or `"Landslide Guardian <onboarding@resend.dev>"`.
  - **Verified**: Yes.

---

## 3. Configuration & Runtime Differences

### Development vs. Production

| Parameter / Behavior | Development (Local) | Production (Railway + Vercel) |
| :--- | :--- | :--- |
| **API Host Binding** | Binds to `0.0.0.0:8000` or `127.0.0.1:8000` with `--reload` | Binds to `0.0.0.0:${PORT}` without `--reload` |
| **Frontend Host Origin** | Localhost: `http://localhost:8000/api` | Vercel proxies `/api/*` to `https://landslideguardian-production.up.railway.app/api/*` |
| **Static Assets** | Served by FastAPI `app.mount("/", StaticFiles(...))` | Served by Vercel Edge CDN using root rewrites to `/frontend/$1` |
| **CORS Policy** | `allow_origins=["*"]` (open for development and cross-origin demo) | `allow_origins=["*"]` (same CORS middleware in `backend/main.py`) |
| **Cache Headers** | Standard browser caching | Vercel enforces `Cache-Control: no-cache, no-store, must-revalidate` for all routes |
| **Database Persistence** | In-Memory fallback if `MONGODB_URI` unset | Requires persistent MongoDB Atlas connection |
| **Email Dispatch** | Simulation mode returns OTP code in API response when SMTP unconfigured | Production requires valid Brevo, Resend, or SMTP keys |

---

## 4. Secrets Handling

- **Current Implementation**:
  - Secrets are read via `dotenv` from `backend/.env` or the operating system environment.
  - `.gitignore` specifically excludes `.env`, `backend/.env`, and `backend/.otp_cache.json`.
  - `.env.example` provides non-sensitive template values.
- **Production Secret Provisioning**:
  - In Railway, secrets are configured via Railway Project Settings -> Variables dashboard (`MONGODB_URI`, `ADMIN_SECRET`, `BREVO_API_KEY`, etc.).
  - In Vercel, no direct backend secrets are required because Vercel only executes static frontend routing with rewrites to Railway.
- **Gaps / Insecure Defaults**:
  - Hardcoded default fallback for `ADMIN_USERNAME` is `"admin"`.
  - Hardcoded default fallback for `ADMIN_PASSWORD` is `"guardian-demo"`.
  - Hardcoded default fallback for `ADMIN_SECRET` is `"change-this-sih-secret"`.
  - If production environment variables are not explicitly injected, the backend boots with these insecure defaults.

---

## 5. Required Services & External Dependencies

| Dependency / Service | Protocol / Interface | Required / Optional | Verified Status |
| :--- | :--- | :--- | :--- |
| **Python 3.10+ / 3.12+** | Local runtime | Required | Verified in virtualenv `.venv` |
| **MongoDB Atlas** | TCP / SRV (`mongodb+srv://`) | Optional (graceful fallback to memory mode) | Verified via `db_manager.ping()` |
| **Open-Meteo Weather API** | HTTPS (`api.open-meteo.com`) | Required for live weather ingestion | Verified in `backend/services/weather_service.py` |
| **Brevo API / Resend API / SMTP** | HTTPS / TLS | Optional (graceful fallback to simulation mode) | Verified in `backend/services/notification_service.py` |
| **Railway Nixpacks** | Container Builder | Required for Railway deployment | Verified in `railway.json` |
| **Vercel Edge Platform** | Static hosting & rewrites | Required for frontend URL | Verified in `vercel.json` |

---

## 6. What is Verified vs. Unknown

- **VERIFIED**:
  - Environment variables inspected directly from source code and `.env.example`.
  - Local runtime behavior verified on Windows Python 3.12 environment.
  - Vercel rewrite rules to Railway backend verified in `vercel.json`.
  - Railway start command verified in `railway.json` and `Procfile`.
- **UNKNOWN / NEEDS CONFIRMATION**:
  - Exact Railway subscription tier, persistent disk configuration, or resource limits (CPU/RAM).
  - Exact Vercel project configuration beyond the checked-in `vercel.json`.
  - Staging environment: None exists in repository.
