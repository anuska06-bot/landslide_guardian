from fastapi import APIRouter, HTTPException, Header
from ..database.mongodb import db_manager, clean_document
from ..models.schemas import CitizenRegisterRequest, SOSBroadcastRequest, TestEmailRequest
from ..services.monitor import find_verified_recipients
from ..services.notification_service import dispatch_email_sos, send_plain_email, _smtp_configured, _get_smtp_config
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
    result = dispatch_email_sos(req.location, matching, req.custom_message)
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
    host, user, password, port, sender = _get_smtp_config()
    smtp_ok = _smtp_configured()

    if not smtp_ok:
        return {
            "status": "NOT_CONFIGURED",
            "message": "SMTP credentials missing.",
            "diagnostics": {
                "smtp_host": host or "Not set",
                "smtp_port": port,
                "smtp_user": user or "Missing",
                "smtp_password_set": bool(password),
                "guide": "Set SMTP_USER and SMTP_PASSWORD (Google App Password) in backend/.env or Railway variables."
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

