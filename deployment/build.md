# Build & Compilation Guide

This document details the build procedures, prerequisites, dependency installation processes, and artifact generation rules verified for Landslide Guardian.

---

## 1. Prerequisites

### Local Development / Windows Host
- **Python**: Version 3.10, 3.11, or 3.12 (Python 3.12.x verified locally in `.venv`).
- **Package Manager**: `pip` (bundled with Python).
- **Virtual Environment**: Standard `venv` module.
- **Node.js / npm**: **NOT REQUIRED**. The frontend contains no npm dependencies, webpack, vite, or transpilation steps. It uses vanilla HTML/CSS/JavaScript with CDN-hosted dependencies (Tailwind, Leaflet).

### Cloud Build Runtime (Railway)
- **Engine**: Nixpacks builder (configured in `railway.json`).
- **Nixpacks Detection**: Automatically detects Python via root `requirements.txt` and `Procfile`.

---

## 2. Dependency Installation

The repository contains two dependency definition files:
1. `requirements.txt` (root directory)
2. `backend/requirements.txt` (backend directory)

Both files specify the following locked/ranged dependencies:

```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.0
python-dotenv>=1.0.0
httpx>=0.27.0
pymongo>=4.6.0
scikit-learn>=1.4.0
numpy>=1.26.0
joblib>=1.3.2
python-multipart>=0.0.9
```

### Installation Commands

#### On Windows:
```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

#### On Linux / macOS / POSIX:
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r backend/requirements.txt
```

---

## 3. Build & Artifact Generation

### Machine Learning Model Generation
The project relies on a pre-trained scikit-learn `ExtraTreesClassifier` model artifact:
- **Output Artifact**: `backend/ml/model.pkl` (~32.0 MB)
- **Source Dataset**: `backend/ml/real_landslide_50k_dataset.csv` (~5.24 MB)
- **Training Script**: `backend/ml/train_model.py`

#### Command to Train/Rebuild Model:
```bash
python -m backend.ml.train_model
```

#### Verified Behavior:
- When executed, `train_model.py` reads `real_landslide_50k_dataset.csv`, fits a 300-estimator `ExtraTreesClassifier` with StandardScaler, evaluates classification metrics, and exports `model.pkl`.
- **Note on Git Tracking**: `backend/ml/model.pkl` is currently committed directly to git. Rebuilding the model is only required if the underlying dataset or feature hyperparameters are modified.

### Frontend Compilation
- **Compilation Steps**: **None**.
- The frontend assets in `frontend/` (`index.html`, `map.html`, `alerts.html`, `assessment.html`, `dashboard.html`, `report.html`, `history.html`, `admin.html`, `css/style.css`, `api.js`, `ui.js`, `map.js`, etc.) are served verbatim. No bundling or minification build pipeline exists.

### Uploads Directory Preparation
- The backend serves and writes crowdsourced images to `backend/uploads/`.
- `backend/main.py` automatically ensures the directory exists at runtime:
  ```python
  UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
  UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
  ```
- The directory is tracked in git via `backend/uploads/.gitkeep`.

---

## 4. Platform-Specific Build Automation

### Windows Batch Scripts
- `install.bat`:
  Automates the initial setup on Windows machines:
  1. Creates `.venv` if not present.
  2. Upgrades `pip`.
  3. Installs dependencies from `backend/requirements.txt`.
  4. Executes `python -m backend.ml.train_model` to generate `backend/ml/model.pkl`.
- `start_server.bat`:
  Executes runtime startup:
  1. Detects Python executable in `.venv`, `venv`, or system PATH.
  2. Runs `pip install -r backend/requirements.txt --quiet`.
  3. Launches default web browser to `http://127.0.0.1:8000/`.
  4. Spawns `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`.

### Cloud Container Build (Railway Nixpacks)
Railway reads `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```
During the build phase, Nixpacks provisions Python and installs `requirements.txt`. No custom build command is configured in `railway.json`.

---

## 5. Build Verification Steps

To verify that the build environment is sound, run the verified test suite:

```bash
# Execute from project root:
python -m unittest discover -s backend -t . -p "test_*.py"
```

### Verified Test Outcome:
- Executes 15 test cases spanning:
  - `backend/test_sih_compliance.py` (10 tests: ML inference, Mohr-Coulomb Factor of Safety, pore pressure calculation, multilingual alert generation, corridor schemas)
  - `backend/test_regional_system.py` (5 tests: 8 NER region configurations, sublocation lookups, spatial grids)
- All 15 tests must finish with `OK` status.
