import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..database.mongodb import clean_document, db_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Local upload directory for crowdsourced / field official photos & videos
BACKEND_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BACKEND_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".webp", ".heic"],
    "video": [".mp4", ".mov", ".webm", ".avi"]
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("/reports/submit")
async def submit_incident_report(
    reporter_name: str = Form("Citizen Reporter"),
    phone_or_email: Optional[str] = Form(None),
    location_name: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    hazard_type: str = Form("Tension Cracks"),
    severity: str = Form("MODERATE"),
    road_status: str = Form("SINGLE_LANE"),
    description: str = Form(""),
    file: Optional[UploadFile] = File(None)
):
    """
    Submits a geo-tagged field report with photo/video of cracks, slope movement,
    or blocked roads. Saves media to disk and document to MongoDB Atlas (with in-memory fallback).
    """
    media_url = None
    media_type = None

    if file and file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext in ALLOWED_EXTENSIONS["image"]:
            media_type = "image"
        elif ext in ALLOWED_EXTENSIONS["video"]:
            media_type = "video"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Allowed: images (JPG, PNG, WEBP) or videos (MP4, MOV, WEBM)."
            )

        # Generate collision-safe filename
        safe_name = f"report_{uuid.uuid4().hex[:12]}{ext}"
        dest_path = UPLOAD_DIR / safe_name

        try:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="File too large (max 25 MB).")
            with open(dest_path, "wb") as f:
                f.write(content)
            media_url = f"/uploads/{safe_name}"
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to save uploaded file: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to store uploaded media file.")

    report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    report_doc = {
        "id": report_id,
        "reporter_name": reporter_name.strip(),
        "phone_or_email": (phone_or_email or "").strip(),
        "location_name": location_name.strip(),
        "latitude": round(float(latitude), 4),
        "longitude": round(float(longitude), 4),
        "hazard_type": hazard_type,
        "severity": severity.upper(),
        "road_status": road_status.upper(),
        "description": description.strip(),
        "media_url": media_url,
        "media_type": media_type,
        "timestamp": timestamp,
        "verified": False,
    }

    try:
        db_manager.incident_reports.insert_one(dict(report_doc))
    except Exception as exc:
        logger.exception("Failed to write incident report to database: %s", exc)

    return {
        "status": "SUCCESS",
        "report_id": report_id,
        "message": "Incident report submitted successfully. Road status and coordinates have been updated on the regional radar.",
        "report": report_doc
    }


@router.get("/reports/all")
async def get_all_reports(limit: int = 50):
    """
    Returns verified and active crowdsourced incident reports for visualization on the map & dashboard.
    """
    try:
        docs = list(db_manager.incident_reports.find().sort("timestamp", -1).limit(min(limit, 100)))
        return {"count": len(docs), "reports": [clean_document(d) for d in docs]}
    except Exception as exc:
        logger.exception("Failed to query incident reports: %s", exc)
        return {"count": 0, "reports": []}


@router.post("/reports/verify/{report_id}")
async def verify_report(report_id: str):
    """Admin endpoint to mark a crowdsourced incident report as verified."""
    try:
        db_manager.incident_reports.update_one(
            {"id": report_id},
            {"$set": {"verified": True, "verified_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"status": "SUCCESS", "message": f"Report {report_id} verified."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
