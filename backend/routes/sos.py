from fastapi import APIRouter, HTTPException, Header
from ..database.mongodb import db_manager, clean_document
from ..models.schemas import CitizenRegisterRequest, SOSBroadcastRequest, TestEmailRequest
from ..services.monitor import find_verified_recipients, auto_dispatch
from ..services.notification_service import (
    dispatch_email_sos, send_plain_email, _smtp_configured, _get_smtp_config, process_offline_sos_queue
)
from ..services.otp_service import clear_otp_rate_limit

router = APIRouter()


@router.post("/sos/register")
async def register_citizen(citizen: CitizenRegisterRequest):
    try:
        doc = citizen.model_dump()
        doc["email_verified"] = False
        doc["account_status"] = "PENDING_VERIFICATION"
        db_manager.citizens.update_one(
            {"email": citizen.email.lower(), "location": citizen.location},
            {"$set": {**doc, "email": citizen.email.lower()}},
            upsert=True,
        )
        clear_otp_rate_limit(citizen.email.lower())
        return {
            "status": "SUCCESS",
            "message": f"Registered {citizen.name} for {citizen.location} email alerts. Email verification required before receiving SOS.",
            "email_verified": False,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not save registration.") from exc


def _admin_required(authorization: str | None):
    from ..services.admin_auth import verify_token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Admin authentication required.")
    if not verify_token(authorization[7:]):
        raise HTTPException(status_code=401, detail="Invalid or expired admin session.")


@router.get("/sos/registrations")
async def registrations(authorization: str | None = Header(default=None)):
    _admin_required(authorization)
    docs = list(db_manager.citizens.find({}, {"_id": 0}))
    return {"count": len(docs), "registrations": [clean_document(d) for d in docs]}


@router.post("/sos/dispatch")
async def dispatch_sos_alert(req: SOSBroadcastRequest, authorization: str | None = Header(default=None)):
    _admin_required(authorization)
    # Admin-only MANUAL dispatch — sends only to VERIFIED registered residents
    # whose city/area or region matches the alert location.
    matching = find_verified_recipients(req.location, "")
    # Count unverified residents matching by location so admin sees the gap.
    lk = req.location.strip().lower()
    unverified = sum(
        1 for u in db_manager.citizens.find()
        if u.get("email_verified") is not True and lk in (u.get("location") or u.get("region") or "").lower()
    )
    result = dispatch_email_sos(req.location, matching, req.custom_message, lang=req.language)
    result["unverified_excluded"] = unverified
    if not matching:
        result["status"] = "NO_VERIFIED_RECIPIENTS"
        result["note"] = "No EMAIL-VERIFIED residents registered for this region yet. Register and verify residents to enable SOS."
    return result


@router.post("/sos/test-email")
async def test_email(req: TestEmailRequest):
    """
    Diagnostic endpoint to send a sample alert message to any recipient email,
    confirming that the SMTP host, user, and App Password are functioning properly.
    """
    host, user, password, port, sender, resend_key, brevo_key = _get_smtp_config()
    smtp_ok = _smtp_configured()

    if not smtp_ok:
        return {
            "status": "NOT_CONFIGURED",
            "message": "Email credentials missing.",
            "diagnostics": {
                "smtp_host": host or "Not set",
                "smtp_port": port,
                "smtp_user": user or "Missing",
                "smtp_password_set": bool(password),
                "resend_configured": bool(resend_key),
                "guide": "Set RESEND_API_KEY (recommended for Railway) or SMTP_USER/SMTP_PASSWORD in Railway variables."
            }
        }

    subject = "⛰️ Landslide Guardian — SMTP Diagnostic Test"
    body = (
        "LANDSLIDE GUARDIAN — EMAIL DIAGNOSTIC TEST\n"
        "==========================================\n\n"
        "Hello,\n\n"
        "This is an automated test message from your Landslide Guardian system.\n"
        "If you are reading this, your SMTP connection and authentication succeeded!\n\n"
        f"Server Host : {host}:{port}\n"
        f"Sender User : {user}\n"
        f"Recipient   : {req.email}\n"
        "System      : SIH Landslide Early Warning System\n\n"
        "Emergency SOS dispatches and citizen OTP verifications are now active."
    )

    res = send_plain_email(req.email, subject, body)
    res["smtp_host"] = host
    res["smtp_port"] = port
    res["smtp_user"] = user
    return res


@router.get("/sos/outbox")
async def get_sos_outbox():
    """Returns queued offline emergency alerts and outbox status."""
    docs = list(db_manager.offline_sos_queue.find().sort("timestamp", -1).limit(50))
    pending_count = db_manager.offline_sos_queue.count_documents({"status": "QUEUED_FOR_RETRY"})
    delivered_count = db_manager.offline_sos_queue.count_documents({"status": "DELIVERED"})
    simulated_count = db_manager.offline_sos_queue.count_documents({"status": "SIMULATED_DISPATCHED"})
    return {
        "status": "ONLINE",
        "pending_count": pending_count,
        "delivered_count": delivered_count,
        "simulated_count": simulated_count,
        "total_queued": len(docs),
        "recent_queue": [clean_document(d) for d in docs],
    }


@router.post("/sos/process-outbox")
async def process_outbox_endpoint():
    """Trigger an immediate processing cycle for pending offline alerts."""
    res = process_offline_sos_queue(limit=20)
    return {
        "status": "PROCESSED",
        "result": res,
    }


@router.post("/sos/test-auto-dispatch")
async def test_auto_dispatch_endpoint(location: str = "Gangtok, Sikkim", risk_score: int = 88, risk_level: str = "CRITICAL"):
    """
    End-to-end verification endpoint: triggers the Auto SOS pipeline for any sector,
    verifying recipient matching, smart cooldown bypass, and delivery/offline queuing.
    """
    res = auto_dispatch(
        location=location,
        risk_score=risk_score,
        risk_level=risk_level,
        recommendation="Mandatory evacuation of downstream zones.",
        region_id="sikkim",
        rainfall=65.0,
        force=True,
    )
    return res

