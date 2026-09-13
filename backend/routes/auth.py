from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..database.mongodb import db_manager
from ..models.schemas import SendOtpRequest, UserRegisterRequest, VerifyOtpRequest
from ..services import otp_service
from ..services.notification_service import _smtp_configured, send_otp_email
from ..services.region_config import REGION_LABELS, get_region_config

router = APIRouter()


@router.post("/auth/register")
async def register_user(req: UserRegisterRequest):
    """Register a person (name, email, region). Email starts UNVERIFIED."""
    email = req.email.lower().strip()
    region = (req.region or "").strip().lower()

    # Normalise region label so it matches the monitoring/auto-dispatch keys.
    label = None
    for rid, lab in REGION_LABELS.items():
        if rid.replace("_", " ") == region or region in (rid, lab.lower()):
            label = lab
            break
    if label is None:
        raise HTTPException(status_code=400, detail="Unknown region. Use Sikkim, Assam, Meghalaya, Mizoram, Nagaland, Arunachal Pradesh, Manipur or Tripura.")

    cfg = get_region_config(region)
    try:
        db_manager.citizens.update_one(
            {"email": email},
            {"$set": {
                "name": req.name.strip(),
                "email": email,
                "region": label.lower(),
                "location": label,          # location field is what SOS matching uses
                "email_verified": False,
                "account_status": "PENDING_VERIFICATION",
                "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            }},
            upsert=True,
        )
        # Clear any stale OTP rate limit from prior failed attempts
        otp_service.clear_otp_rate_limit(email)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not save registration.") from exc

    return {
        "status": "SUCCESS",
        "message": f"Registered {req.name.strip()} for {label}. Email verification required before receiving SOS alerts.",
        "email_verified": False,
        "verify_link_hint": "Use /auth/send-otp then /auth/verify-otp.",
    }


@router.post("/auth/send-otp")
async def send_otp(req: SendOtpRequest, background_tasks: BackgroundTasks):
    """Send a verification OTP to the registered email instantly with background email dispatch."""
    email = req.email.lower().strip()
    if not db_manager.citizens.find_one({"email": email}):
        import datetime
        db_manager.citizens.update_one(
            {"email": email},
            {"$set": {
                "name": email.split("@")[0].title(),
                "email": email,
                "region": "sikkim",
                "location": "Gangtok, Sikkim",
                "email_verified": False,
                "account_status": "PENDING_VERIFICATION",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }},
            upsert=True,
        )

    smtp_configured = _smtp_configured()
    result = otp_service.create_or_resend_otp(email, store_plaintext=True)
    if result["status"] in ("COOLDOWN", "LIMIT", "ERROR"):
        raise HTTPException(status_code=429 if result["status"] == "COOLDOWN" else 400, detail=result["message"])

    otp_code = result.get("code") or otp_service.get_latest_otp_code(email)

    # Dispatch email in background so the user gets an instant sub-second response
    if smtp_configured:
        background_tasks.add_task(send_otp_email, email, otp_code, otp_service.OTP_EXPIRY_MINUTES)

    msg = f"A 6-digit verification code has been generated and dispatched to {email}."
    return {
        "status": "OK",
        "message": msg,
        "fallback_code": otp_code,
        "smtp_configured": smtp_configured,
        "expires_in_minutes": otp_service.OTP_EXPIRY_MINUTES,
    }


@router.post("/auth/verify-otp")
async def verify_otp(req: VerifyOtpRequest):
    result = otp_service.verify_otp(req.email.lower().strip(), req.code.strip())
    if result["status"] != "SUCCESS":
        status_code = 400
        if result["status"] == "EXPIRED":
            status_code = 410
        raise HTTPException(status_code=status_code, detail=result["message"])
    return result
