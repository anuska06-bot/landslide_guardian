import html
import logging
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"
load_dotenv(ENV_FILE)
load_dotenv()

logger = logging.getLogger(__name__)

def _get_smtp_config():
    host = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER", "smtp.gmail.com")
    user = os.getenv("SMTP_USER") or os.getenv("SMTP_EMAIL", "")
    password = os.getenv("SMTP_PASSWORD", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    sender = os.getenv("ALERT_FROM_EMAIL") or user
    return host, user, password, port, sender

def _smtp_configured():
    host, user, password, _, _ = _get_smtp_config()
    return bool(host and user and password)


def _send(recipient: str, subject: str, body: str) -> dict:
    host, user, password, port, sender = _get_smtp_config()
    if not (user and password):
        print(f"[SMTP WARNING] Credentials missing. Simulated send to: {recipient}")
        return {
            "status": "NOT_CONFIGURED",
            "recipient": recipient,
            "message": "SMTP credentials (SMTP_USER and SMTP_PASSWORD) are not configured in backend/.env."
        }

    clean_password = password.strip().replace(" ", "")
    clean_user = user.strip()
    target_recipient = recipient.strip()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Landslide Guardian <{sender.strip()}>"
    msg["To"] = target_recipient
    msg.set_content(body)

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=15) as server:
                server.login(clean_user, clean_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(clean_user, clean_password)
                server.send_message(msg)
        print(f"[SMTP SUCCESS] Email successfully sent to -> {target_recipient}")
        return {"status": "SENT", "recipient": target_recipient}
    except smtplib.SMTPAuthenticationError as auth_err:
        err_msg = (
            f"SMTP Authentication failed for '{clean_user}'. "
            "If using Gmail, you MUST generate and use a 16-character App Password "
            "(Google Account -> Security -> 2-Step Verification -> App Passwords), NOT your normal Google password."
        )
        print(f"[SMTP AUTH ERROR] {err_msg}")
        logger.warning(err_msg)
        return {"status": "AUTH_FAILED", "recipient": target_recipient, "error": err_msg}
    except Exception as exc:
        print(f"[SMTP ERROR] Failed sending to {target_recipient}: {exc}")
        logger.exception("Email dispatch failed to %s", target_recipient)
        return {"status": "FAILED", "recipient": target_recipient, "error": str(exc)}


def send_plain_email(recipient: str, subject: str, body: str) -> dict:
    """Generic send used for OTP verification and other non-SOS emails."""
    return _send(recipient, subject, body)


def send_otp_email(recipient: str, otp_code: str, expiry_minutes: int = 10) -> dict:
    subject = "Landslide Guardian — Email Verification Code"
    body = (
        "LANDSLIDE GUARDIAN — EMAIL VERIFICATION\n"
        "--------------------------------------\n\n"
        f"Your verification code is: {otp_code}\n\n"
        f"This code expires in {expiry_minutes} minutes and is valid for a "
        "limited number of attempts.\n\n"
        "If you did not request this, you can ignore this email.\n\n"
        "This is required to activate your emergency landslide alert "
        "registration with the Landslide Guardian system."
    )
    return _send(recipient, subject, body)


def send_alert_email(recipient: str, location: str, message: str, risk_score=None, risk_level=None):
    subject = f"🚨 URGENT LANDSLIDE SOS ALERT — {location} [{risk_level or 'HIGH RISK'}]"
    score_line = f"Calculated Risk: {risk_score}% ({risk_level})" if risk_score is not None else "Emergency SOS Notification"
    ts = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")

    body = f"""================================================================================
🚨 LANDSLIDE GUARDIAN — AUTOMATIC REGIONAL SOS DISPATCH
================================================================================
Target Sector   : {location}
Alert Level     : {risk_level or 'HIGH/CRITICAL'}
Geotech Risk    : {score_line}
Timestamp       : {ts}
Recipient       : {recipient} (Verified Resident / Community Monitor)

--------------------------------------------------------------------------------
⚠️ SENSOR & TELEMETRY WARNING SUMMARY:
--------------------------------------------------------------------------------
{message}

--------------------------------------------------------------------------------
🛡️ IMMEDIATE ACTION PROTOCOL — WHAT YOU MUST DO RIGHT NOW:
--------------------------------------------------------------------------------
1. EVACUATE HIGH-RISK ZONES IMMEDIATELY:
   • Move away from the direct path of steep slopes, cliffs, natural ravines, 
     drainage gullies, and freshly exposed road-cut slopes.
   • If indoors and sudden rumbling or shaking begins, move to the HIGHEST level 
     of the building or the side facing AWAY from the hill slope.

2. AVOID ALL HIGHWAY / MOUNTAIN TRANSIT:
   • Mountain corridors in this sector (NH routes and hill bypasses) are subject 
     to sudden rockfall, debris flows, and cut-slope collapses.
   • Never attempt to cross flooded causeways or moving debris streams.

3. RECOGNIZE IMMINENT WARNING SIGNS:
   • New tension cracks appearing in the ground, walls, or pavements.
   • Tilting trees, utility poles, or fences.
   • Rapid muddying or sudden changes in stream water levels.
   • Faint rumbling sounds that increase in volume.

--------------------------------------------------------------------------------
🎒 PREPARE YOUR EMERGENCY GRAB-AND-GO KIT:
--------------------------------------------------------------------------------
   [✓] Essential prescription medications, first aid kit, and water purification.
   [✓] Crucial identity documents, property papers, and cash in a waterproof pouch.
   [✓] High-lumen LED flashlight, battery bank, and battery-powered FM/AM radio.
   [✓] Minimum 72-hour non-perishable food rations and 3 litres of drinking water per person.
   [✓] Sturdy mountain footwear, warm rainproof clothing, and whistle for signaling.

--------------------------------------------------------------------------------
📞 EMERGENCY HELPLINES & HOW TO SEEK RESCUE:
--------------------------------------------------------------------------------
   • National Unified Emergency Helpline   : 112 (Police / Fire / Medical)
   • State Disaster Management Authority   : 1070
   • District Emergency Operations Centre  : 1077
   • Ambulance Emergency Service           : 108
   • National Disaster Response Force (NDRF): 011-24363260 / 9711077372

Stay tuned to official disaster broadcasts via SACHET (NDMA) and local civil authorities.
Do not return to evacuated slopes until local geological authorities declare the sector stable.

================================================================================
Landslide Guardian Autonomous Radar System · Northeast Regional Monitoring
This message was triggered automatically by 15-minute regional IoT telemetry scans.
================================================================================
"""
    return _send(recipient, subject, body)

def dispatch_email_sos(location: str, users: list, custom_msg: str = None, risk_score=None, risk_level=None):
    timestamp = datetime.now(timezone.utc).isoformat()
    message = custom_msg or (
        f"Landslide risk has reached the emergency notification threshold near {location}. "
        "Please move away from unstable slopes, drainage channels, and exposed cut slopes, "
        "and initiate local safety protocols immediately."
    )
    
    logs = []
    for user in users:
        email = user.get("email", "") if isinstance(user, dict) else str(user)
        if not email:
            continue
        
        name = user.get("name", "Resident / Responder") if isinstance(user, dict) else "Resident"
        result = send_alert_email(email, location, message, risk_score, risk_level)
        logs.append({
            "name": name,
            "email": email,
            **result,
            "timestamp": timestamp,
        })

    statuses = [x["status"] for x in logs]
    if not logs:
        status = "NO_RECIPIENTS"
    elif any(s == "SENT" for s in statuses):
        status = "SENT"
    elif all(s == "NOT_CONFIGURED" for s in statuses):
        status = "SMTP_NOT_CONFIGURED"
    else:
        status = "FAILED"

    return {
        "status": status,
        "location": location,
        "recipient_count": len(logs),
        "timestamp": timestamp,
        "logs": logs,
        "smtp_configured": _smtp_configured(),
        "note": "Ensure SMTP_USER and SMTP_PASSWORD (Google App Password) are set in backend/.env"
    }