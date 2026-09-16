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


VALID_STATUSES = ["SUBMITTED", "UNDER_REVIEW", "VERIFIED", "REJECTED", "RESOLVED"]


def calculate_response_priority(severity: str, road_status: str, location_name: str) -> str:
    """
    Computes objective emergency response priority (P1 to P4):
    - P1: Life-safety or total arterial highway blockage (Lifeline cut off)
    - P2: High risk or major bottleneck constriction
    - P3: Moderate geotechnical tension cracks / partial encroachment
    - P4: Low/advisory report under monitoring
    """
    loc_lower = (location_name or "").lower()
    is_lifeline = any(kw in loc_lower for kw in ["nh-", "highway", "corridor", "lifeline", "tupul", "singtam", "durtlang", "sevoke"])
    sev = (severity or "MODERATE").upper()
    road = (road_status or "FULLY_OPEN").upper()

    if sev == "CRITICAL" or road == "BLOCKED":
        return "P1_EMERGENCY" if is_lifeline else "P1_HIGH_IMPACT"
    if sev == "HIGH" or road in ("SINGLE_LANE", "ESCORT_ONLY"):
        return "P2_URGENT"
    if sev == "MODERATE":
        return "P3_ATTENTION"
    return "P4_ADVISORY"


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
    priority = calculate_response_priority(severity, road_status, location_name)

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
        "status": "SUBMITTED",
        "verification_status": "UNVERIFIED",
        "verified": False,
        "response_priority": priority,
        "confirmation_status": "UNCONFIRMED_CITIZEN_REPORT",
        "disclaimer": "Crowdsourced report awaiting official ground inspection by disaster response authorities.",
    }

    try:
        db_manager.incident_reports.insert_one(dict(report_doc))
    except Exception as exc:
        logger.exception("Failed to write incident report to database: %s", exc)

    return {
        "status": "SUCCESS",
        "report_id": report_id,
        "message": "Incident report submitted successfully. Road status logged under review.",
        "response_priority": priority,
        "report": report_doc
    }


@router.get("/reports/all")
async def get_all_reports(limit: int = 50, status: Optional[str] = None):
    """
    Returns incident reports filtered by optional lifecycle status (SUBMITTED, UNDER_REVIEW, VERIFIED, RESOLVED).
    """
    try:
        query = {}
        if status:
            query["status"] = status.upper()
        docs = list(db_manager.incident_reports.find(query).sort("timestamp", -1).limit(min(limit, 100)))
        return {"count": len(docs), "reports": [clean_document(d) for d in docs]}
    except Exception as exc:
        logger.exception("Failed to query incident reports: %s", exc)
        return {"count": 0, "reports": []}


@router.patch("/reports/{report_id}/status")
async def update_report_status(report_id: str, new_status: str, notes: Optional[str] = None):
    """
    Official lifecycle transition: SUBMITTED -> UNDER_REVIEW -> VERIFIED -> REJECTED -> RESOLVED.
    """
    new_status = new_status.upper()
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Allowed: {', '.join(VALID_STATUSES)}"
        )

    update_payload = {
        "status": new_status,
        "verification_status": new_status,
        "verified": (new_status == "VERIFIED"),
        "status_updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if notes:
        update_payload["official_notes"] = notes.strip()

    try:
        db_manager.incident_reports.update_one(
            {"id": report_id},
            {"$set": update_payload}
        )
        return {
            "status": "SUCCESS",
            "report_id": report_id,
            "updated_status": new_status,
            "message": f"Report {report_id} transitioned to {new_status}."
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/reports/verify/{report_id}")
async def verify_report(report_id: str):
    """Admin endpoint to mark a crowdsourced incident report as verified."""
    return await update_report_status(report_id, "VERIFIED")


NER_HIGHWAY_CORRIDORS = [
    {"corridor": "NH-10 (Sevoke - Singtam - Gangtok)", "code": "NH-10", "state": "Sikkim", "status": "FULLY_OPEN", "bottlenecks": 0, "priority": "P4_NORMAL"},
    {"corridor": "NH-40 / GS Road (Guwahati - Shillong - Sohra)", "code": "NH-40", "state": "Meghalaya", "status": "FULLY_OPEN", "bottlenecks": 0, "priority": "P4_NORMAL"},
    {"corridor": "NH-29 (Dimapur - Kohima - Mao)", "code": "NH-29", "state": "Nagaland", "status": "FULLY_OPEN", "bottlenecks": 0, "priority": "P4_NORMAL"},
    {"corridor": "NH-37 / Tupul Railway Line (Jiribam - Imphal)", "code": "NH-37", "state": "Manipur", "status": "FULLY_OPEN", "bottlenecks": 0, "priority": "P4_NORMAL"},
    {"corridor": "NH-54 / NH-2 (Aizawl - Lunglei Spine)", "code": "NH-54", "state": "Mizoram", "status": "FULLY_OPEN", "bottlenecks": 0, "priority": "P4_NORMAL"},
    {"corridor": "NH-13 (Trans-Arunachal Highway)", "code": "NH-13", "state": "Arunachal Pradesh", "status": "FULLY_OPEN", "bottlenecks": 0, "priority": "P4_NORMAL"},
    {"corridor": "NH-27 / Haflong Hill Section", "code": "NH-27", "state": "Assam", "status": "FULLY_OPEN", "bottlenecks": 0, "priority": "P4_NORMAL"},
    {"corridor": "NH-8 (Baramura - Agartala)", "code": "NH-8", "state": "Tripura", "status": "FULLY_OPEN", "bottlenecks": 0, "priority": "P4_NORMAL"},
]


@router.get("/reports/roads/status")
async def get_road_connectivity_status():
    """
    Aggregated road connectivity status across major NER highway corridors.
    Combines baseline highway profiles with real-time verified/submitted incident reports.
    """
    try:
        reports = list(db_manager.incident_reports.find({"status": {"$in": ["SUBMITTED", "UNDER_REVIEW", "VERIFIED"]}}).sort("timestamp", -1).limit(100))

        # Copy baseline highway profiles
        import copy
        corridors = copy.deepcopy(NER_HIGHWAY_CORRIDORS)

        # Overlay active incidents on matching corridors
        for r in reports:
            loc = (r.get("location_name") or "").lower()
            road = (r.get("road_status") or "FULLY_OPEN").upper()
            if road in ("BLOCKED", "SINGLE_LANE", "ESCORT_ONLY"):
                for c in corridors:
                    corridor_name = c["corridor"].lower()
                    state_name = c["state"].lower()
                    if any(token in loc for token in corridor_name.split()) or state_name in loc:
                        c["bottlenecks"] += 1
                        if road == "BLOCKED":
                            c["status"] = "BLOCKED"
                            c["priority"] = "P1_EMERGENCY"
                        elif road in ("SINGLE_LANE", "ESCORT_ONLY") and c["status"] != "BLOCKED":
                            c["status"] = road
                            c["priority"] = "P2_URGENT"

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_monitored_corridors": len(corridors),
            "active_disruptions_count": sum(1 for c in corridors if c["status"] != "FULLY_OPEN"),
            "corridors": corridors,
            "recent_incidents": [clean_document(r) for r in reports[:10]],
            "data_provenance": "Aggregated from citizen & field-official observations with automated priority scoring.",
        }
    except Exception as exc:
        logger.exception("Failed to compute road connectivity status: %s", exc)
        return {"error": str(exc), "corridors": []}
