# Landslide Guardian (v3.0.0)

> **AI-Based Multi-Scale Early Warning & Geotechnical Risk Monitoring System for the North Eastern Region (NER)**  
> **Smart India Hackathon 2026 | Problem Statement ID: SIH26001**  
> **Nodal Ministry**: Ministry of Development of North Eastern Region (MDoNER) in coordination with National Disaster Management Authority (NDMA)  
> **Team**: Ctrl+she2.0

---

## 1. Live Deployment & System Status

- **WebGIS Production Frontend**: [https://landslideguardian.vercel.app](https://landslideguardian.vercel.app)
- **API Production Backend**: [https://landslideguardian-production.up.railway.app](https://landslideguardian-production.up.railway.app)
- **System Health Endpoint**: `GET https://landslideguardian-production.up.railway.app/api/health`
- **System Configuration**: `GET https://landslideguardian-production.up.railway.app/api/config`

---

## 2. Key Capabilities & Innovations

- **Tri-Partite Risk Engine**:
  - Combines data-driven machine learning, classical slope mechanics, and hydrological infiltration into a single composite score:
    - **Machine Learning (40% weight)**: Extra Trees Classifier trained on historical geo-environmental terrain data.
    - **Geotechnical Physics (35% weight)**: Infinite-slope Mohr-Coulomb Factor of Safety ($FS$) equation.
    - **Hydrogeology (25% weight)**: Green-Ampt and 1D transient pore-water pressure ($u$) estimation.
- **Continuous 8-State Regional Radar**:
  - 24/7 automated background surveillance covering all eight Northeast states: Sikkim, Assam, Meghalaya, Mizoram, Nagaland, Arunachal Pradesh, Manipur, and Tripura.
  - Re-evaluates risk every 15 minutes using live weather from Open-Meteo and satellite precipitation feeds.
- **Route Guardian for 8 Highway Corridors**:
  - Chainage-level risk tracking sampled every 500 metres along critical arterial mountain corridors:
    - **NH-10**: Siliguri - Gangtok (Lifeline of Sikkim)
    - **NH-40**: Guwahati - Shillong (High-density freight corridor)
    - **NH-29**: Dimapur - Kohima (Pagla Pahar landslide zone)
    - **NH-37**: Jorhat - Dibrugarh (Upper Assam flood-slope link)
    - **NH-54**: Silchar - Aizawl (Mizoram transit artery)
    - **NH-13**: Trans-Arunachal Highway
    - **NH-27**: Silchar - Haflong - Nagaon (Dima Hasao hill section)
    - **NH-8**: Karimganj - Agartala (Tripura lifeline)
- **Zero-Failure Emergency Notification Engine**:
  - Triple-provider failover pipeline: **Brevo HTTP API** (primary) $\rightarrow$ **Resend HTTP API** (secondary) $\rightarrow$ **IPv4 SMTP** (fallback) $\rightarrow$ **Persistent Offline Outbox Queue**.
  - Smart cooldown prevents duplicate notification spam (60-minute default) while automatically bypassing cooldown during critical hazard surges.
  - Generates localized emergency alert templates in 4 languages: **English**, **Hindi**, **Assamese**, and **Bengali**.
- **Offline-First Crowdsourced Hazard Reporting**:
  - PWA architecture enabling field teams, road crews, and citizens to capture geo-tagged hazard photos and ground crack reports without internet access.
  - Stores reports in client-side IndexedDB and automatically syncs to the server when network connectivity is restored.
- **Email OTP Citizen Verification**:
  - Protects alert channels against spam through cryptographic HMAC-SHA256 hashed 6-digit OTP codes. Only verified residents receive automated regional SOS warnings.

---

## 3. System Architecture & Data Flow

```
                                 [ Open-Meteo & NASA GPM ]
                                             │
                                             ▼
[ Physical Geotechnical Profiles ] ──> [ FastAPI Backend ] <── [ Pre-Trained Extra Trees Model ]
(c', φ', γsat, 30m DEM slope)                │                     (94.12% Acc, 98.21% ROC-AUC)
                                             │
                                  [ Tri-Partite Risk Engine ]
                                  ├── ML Susceptibility (40%)
                                  ├── Mohr-Coulomb FS   (35%)
                                  └── Pore Pressure u   (25%)
                                             │
                                             ▼
                                  [ Composite Risk Score ]
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             [ WebGIS Portal (Vercel) ]                 [ Emergency SOS Engine ]
             ├── 8-State Radar Feed                     ├── 4-Language Alerts
             ├── 8 Highway Corridors                    ├── Brevo -> Resend -> SMTP
             └── Offline PWA Reports                    └── Anti-Spam Surge Bypass
```

---

## 4. Scientific Safeguards & Transparency Standards

- **No Synthetic Weather or Tilt Injection**:
  - Real-time weather and rainfall inputs are fetched directly from live numerical weather providers.
  - Ground tilt is strictly isolated as a hardware sensor interface and is never fabricated or simulated in software mode.
- **Pore-Water Pressure vs. Rainfall Distinction**:
  - Pore-water pressure ($u$) is calculated using hydraulic head infiltration physics ($u = \gamma_w \cdot h_w$) and is clearly flagged as an *estimate* requiring site-specific piezometer calibration.
- **Distinction Between Zero Rain and Missing Data**:
  - Verified 0 mm rainfall is treated as a valid low-risk reading (`NO_RAIN`).
  - Provider network outages are marked as `NO_DATA` / `DATA_UNAVAILABLE` and will never declare false alarms or trigger automatic SOS broadcasts.
- **Backend Non-Crashing Resilience**:
  - All external API calls, SMTP network attempts, and database connections are wrapped in structured exception boundaries with persistent local fallbacks.

---

## 5. Technology Stack

- **Backend & Compute**:
  - Python 3.12 / FastAPI (Asynchronous high-throughput REST API)
  - Uvicorn (ASGI web server)
  - Scikit-learn, NumPy, SciPy, Joblib (Machine learning & geotechnical solvers)
  - Pydantic v2 (Strict data validation schemas)
  - SQLAlchemy / PyMongo (Database persistence)
- **Frontend & WebGIS**:
  - Modern HTML5, CSS3, ES6 JavaScript (No heavyweight node build dependencies)
  - Tailwind CSS & FontAwesome (Responsive UI components)
  - Leaflet & React-Leaflet (Interactive mapping, vector tiles, coordinate transforms)
  - Service Workers & IndexedDB (Offline storage & background synchronization)
- **Database & Queueing**:
  - MongoDB Atlas (Cloud database with 13 collections & compound indexes)
  - In-Memory Mock Database (`MemoryDatabase`) fallback for offline testing
  - SQLite persistent local outbox queue (`offline_sos_queue`)
- **Hosting & Infrastructure**:
  - Frontend: Vercel Edge Network (`vercel.json` with reverse-proxy rewrites)
  - Backend: Railway Linux Container (`railway.json` with Nixpacks builder)

---

## 6. Project Structure

```text
Landslide/
├── .env.example                  # Environment configuration template
├── .gitignore                    # Secrets, virtualenv, and build ignore rules
├── Procfile                      # Process declaration for cloud platforms
├── railway.json                  # Railway Nixpacks deployment configuration
├── requirements.txt              # Root Python dependencies
├── vercel.json                   # Vercel static routing and API rewrite rules
├── install.bat                   # 1-click Windows installer (venv + dependencies + ML)
├── start_server.bat              # 1-click Windows server launcher
│
├── api/                          # Serverless entrypoint
│   └── index.py                  # Vercel serverless function wrapper
│
├── backend/                      # Core FastAPI Application
│   ├── main.py                   # App startup, lifespan background worker, route mounts
│   ├── requirements.txt          # Backend dependency declarations
│   ├── test_sih_compliance.py    # SIH26001 compliance verification suite (10 tests)
│   ├── test_regional_system.py   # 8-state regional radar & grid tests (5 tests)
│   ├── test_mongodb.py           # MongoDB Atlas connectivity validation
│   ├── database/
│   │   └── mongodb.py            # MongoDB Atlas manager with in-memory fallback
│   ├── ml/
│   │   ├── model.pkl             # Trained Extra Trees Classifier model (~32 MB)
│   │   ├── predict.py            # Feature scaling & probability inference
│   │   ├── train_model.py        # Model training & cross-validation script
│   │   └── real_landslide_50k_dataset.csv # Curated terrain & hazard dataset
│   ├── models/
│   │   └── schemas.py            # Pydantic schemas (assessments, sensors, alerts)
│   ├── routes/                   # API Route Controllers
│   │   ├── admin.py              # Administrative session management
│   │   ├── alerts.py             # Active warnings and regional radar feeds
│   │   ├── assistant.py          # Explainable AI disaster query engine
│   │   ├── auth.py               # Citizen registration and OTP verification
│   │   ├── dataset.py            # Scientific dataset transparency disclosures
│   │   ├── environment.py        # Open-Meteo live atmospheric readings
│   │   ├── locations.py          # NER focus locations and spatial coordinates
│   │   ├── monitor.py            # Background monitor status, logs, and controls
│   │   ├── pipeline.py           # Interactive early warning pipeline layers
│   │   ├── reports.py            # Crowdsourced hazard incident reporting
│   │   ├── risk.py               # ML risk prediction and evaluations
│   │   ├── sensors.py            # Future IoT hardware sensor ingest endpoint
│   │   └── sos.py                # Citizen alert subscriptions and manual SOS
│   └── services/                 # Business Logic & Engineering Solvers
│       ├── admin_auth.py         # Session token verification
│       ├── geo_hierarchy.py      # Spatial bounds, district hierarchies, grid cells
│       ├── monitor.py            # Autonomous 15-minute background loop
│       ├── multilingual.py       # 4-language alert translation synthesis
│       ├── notification_service.py # Brevo/Resend/SMTP failover notification pipeline
│       ├── otp_service.py        # OTP issuance, cooldown, and HMAC verification
│       ├── pore_pressure.py      # Hydraulic infiltration & pore pressure math
│       ├── rainfall_service.py   # Live weather polling & deduplication
│       ├── region_config.py      # 8 NER state geotechnical site profiles
│       ├── risk_service.py       # Tri-Partite composite risk engine
│       ├── seismic_service.py    # Seismic zone acceleration adjustments
│       ├── terrain_service.py    # Infinite slope Mohr-Coulomb Factor of Safety
│       └── weather_service.py    # Open-Meteo API connector
│
├── frontend/                     # WebGIS User Interface (Vanilla JS + HTML5)
│   ├── index.html                # Landing page with live status banner & overview
│   ├── map.html                  # Interactive GIS map (8 states + 8 highway corridors)
│   ├── assessment.html           # Interactive slope assessment & live testing
│   ├── dashboard.html            # Real-time state-by-state surveillance dashboard
│   ├── alerts.html               # Public alerts feed, OTP registration & emergency SOS
│   ├── report.html               # Crowdsourced hazard report submission (Offline PWA)
│   ├── history.html              # Historical landslide catalog and disaster log
│   ├── admin-login.html          # Administrator login portal
│   ├── admin.html                # Protected administrative control room
│   ├── api.js                    # Dynamic frontend API routing (local vs. Railway)
│   ├── ui.js                     # Shared navigation, toast notifications, UI helpers
│   ├── map.js                    # Leaflet map rendering, GeoJSON layers, corridor lines
│   ├── alerts.js                 # Alerts feed, OTP verification logic, manual SOS
│   ├── assessment.js             # Geotechnical parameter inputs & radar charts
│   ├── report.js                 # Geolocation, camera upload, IndexedDB offline sync
│   ├── css/style.css             # System typography, animations, dark mode theme
│   └── assets/                   # Static imagery and historical incident photography
│
└── deployment/                   # Verified Deployment Documentation Layer
    ├── environments.md           # Runtime parameters, env vars, and secrets
    ├── build.md                  # Prerequisites, dependency setup, and artifacts
    ├── deployment.md             # Multi-cloud deployment architecture & operations
    ├── rollback.md               # Recovery procedures and database rollback gaps
    └── release-checklist.md      # 7-phase production release validation checklist
```

---

## 7. Quickstart & Local Installation

### Prerequisites
- Python 3.10, 3.11, or 3.12 (Python 3.12 verified)
- Git

### Automated Windows Setup
Double-click `install.bat` or run:
```cmd
install.bat
```
Then start the server:
```cmd
start_server.bat
```

### Manual Setup (Cross-Platform / POSIX / macOS)
1. **Clone the repository**:
   ```bash
   git clone https://github.com/anuska06-bot/landslide_guardian.git
   cd landslide_guardian
   ```
2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```
4. **Train the machine learning model** *(Optional - pre-trained `model.pkl` is already included)*:
   ```bash
   python -m backend.ml.train_model
   ```
5. **Configure environment variables**:
   ```bash
   cp .env.example backend/.env
   # Edit backend/.env with your MongoDB and SMTP/Brevo credentials
   ```
6. **Launch the backend server**:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
7. **Access the application**:
   Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your web browser.

---

## 8. Environment Variables Reference

Configure these in `backend/.env` or in your cloud hosting dashboard (e.g., Railway Variables):

| Variable | Description | Default / Example | Required |
| :--- | :--- | :--- | :--- |
| `PORT` | Web server listening port | `8000` | Optional |
| `MONGODB_URI` | MongoDB Atlas SRV connection string | `mongodb+srv://...` | Optional (falls back to memory) |
| `ADMIN_USERNAME` | Administrator portal login username | `admin` | Production Recommended |
| `ADMIN_PASSWORD` | Administrator portal login password | `guardian-demo` | Production Recommended |
| `ADMIN_SECRET` | Cryptographic secret for signing session tokens | `change-this-sih-secret` | Production Recommended |
| `BREVO_API_KEY` | Primary transactional email API key | *(Brevo API Key)* | Optional (enables real email) |
| `RESEND_API_KEY` | Secondary failover email API key | *(Resend API Key)* | Optional |
| `SMTP_HOST` | Fallback SMTP server host | `smtp.gmail.com` | Optional |
| `SMTP_PORT` | Fallback SMTP port (SSL) | `465` (or `587`) | Optional |
| `SMTP_USER` | Fallback SMTP username / email address | `user@gmail.com` | Optional |
| `SMTP_PASSWORD` | Fallback SMTP App Password | `xxxx xxxx xxxx xxxx` | Optional |
| `ALERT_FROM_EMAIL` | Sender address shown in emergency emails | `user@gmail.com` | Optional |
| `MONITOR_INTERVAL_MINUTES`| Background surveillance loop frequency | `15` | Optional |
| `SOS_COOLDOWN_MINUTES` | Cooldown between automated alerts to same region | `60` | Optional |
| `OTP_SALT` | Salt used to HMAC-hash verification OTPs | `landslide-guardian-otp-salt` | Production Recommended |

---

## 9. Comprehensive API Reference

### Health & Runtime Configuration
- `GET /api/health`: Comprehensive system health, version, and database connection status.
- `GET /api/config`: Current operational parameters, storage mode, region count, and monitoring interval.

### Risk Prediction & ML Engine
- `POST /api/risk/evaluate`: Evaluate multi-factor landslide hazard for specific coordinates.
- `POST /api/risk/predict`: Raw Extra Trees model probability inference.
- `GET /api/risk/latest`: Latest computed risk score and hazard level.
- `GET /api/risk/all`: Historical risk assessments across all monitored areas.

### Regional Surveillance & Highways
- `GET /api/alerts/regional-radar`: Real-time hazard overview across all 8 NER states.
- `GET /api/alerts/active`: Active warnings feed filtered by urgency (Critical, High, Moderate).
- `GET /api/pipeline/corridors`: Real-time status and risk scores for all 8 national highway corridors.
- `GET /api/locations`: Curated list of high-risk mountain coordinates and focus areas.

### Weather & Hydrogeology
- `GET /api/weather/ner`: Current atmospheric readings and forecasts across focus centers.
- `GET /api/rainfall/live`: Live precipitation measurement with duplicate protection.
- `POST /api/pore-pressure/calculate`: Transient pore pressure estimation from rainfall history.

### Citizen Alert Subscriptions & Automated SOS
- `POST /api/auth/register`: Register resident details (name, email, location).
- `POST /api/auth/send-otp`: Transmit 6-digit verification code to citizen email.
- `POST /api/auth/verify-otp`: Validate submitted OTP and mark citizen verified.
- `POST /api/sos/dispatch`: Admin-only emergency alert broadcast.

### Crowdsourced Hazard Reports (Offline PWA)
- `POST /api/reports/submit`: Submit field incident report with geo-coordinates, crack width, and photo.
- `GET /api/reports/list`: Retrieve recent citizen reports with priority sorting.

### Explainable AI Assistant
- `POST /api/assistant/ask`: Query the AI disaster assistant regarding current regional slope risks.

---

## 10. Verification & Test Suite

The project includes an automated test suite verifying compliance with the official SIH26001 specification:

```bash
# Run all verified tests from the project root:
python -m unittest discover -s backend -t . -p "test_*.py"
```

### Verified Test Results (15/15 Passing):
- **10 Compliance Tests (`test_sih_compliance.py`)**:
  - Extra Trees model inference & probability boundaries.
  - Infinite Slope Mohr-Coulomb Factor of Safety physics.
  - Hydrogeological pore water pressure estimation.
  - Scientific dataset provenance and transparency disclosures.
  - Multilingual alert template generation (English, Hindi, Assamese, Bengali).
  - Citizen report response priority calculation across 5 tiers.
  - Highway corridor status tracking across all 8 NER routes.
  - Historical disaster catalog integrity.
  - Future IoT sensor reading schema validation.
  - Real-time weather to risk assessment end-to-end integration.
- **5 Regional Radar Tests (`test_regional_system.py`)**:
  - Verification of all 8 NER state configurations.
  - Sublocation lookup and coordinate resolution (e.g., Rimbi, Singlitam, Mawlai, Tupul).
  - Spatial search and autocomplete indexing.
  - Dynamic regional bounding box grid cell generation.
  - Coordinate-specific risk differentiation under identical rainfall.

---

## 11. Deployment Documentation

For detailed guides on production environments, compilation, and cloud deployment:
- [environments.md](file:///c:/Users/ANUSKA/OneDrive/Desktop/Landslide_Final/Landslide/deployment/environments.md): Complete environment variable dictionary and runtime configurations.
- [build.md](file:///c:/Users/ANUSKA/OneDrive/Desktop/Landslide_Final/Landslide/deployment/build.md): Prerequisites, build scripts, ML model compilation, and artifacts.
- [deployment.md](file:///c:/Users/ANUSKA/OneDrive/Desktop/Landslide_Final/Landslide/deployment/deployment.md): Multi-cloud architecture (Vercel + Railway) and step-by-step setup.
- [rollback.md](file:///c:/Users/ANUSKA/OneDrive/Desktop/Landslide_Final/Landslide/deployment/rollback.md): Recovery procedures, auto-healing policies, and database rollback notes.
- [release-checklist.md](file:///c:/Users/ANUSKA/OneDrive/Desktop/Landslide_Final/Landslide/deployment/release-checklist.md): 7-phase pre-release and post-release validation checklist.