import html
import logging
import os
import socket
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from pathlib import Path
import httpx
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"
load_dotenv(ENV_FILE)
load_dotenv()

logger = logging.getLogger(__name__)


class IPv4SMTP(smtplib.SMTP):
    """SMTP client forcing IPv4 address resolution to prevent [Errno 101] Network is unreachable in cloud containers."""
    def _get_socket(self, host, port, timeout):
        try:
            infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
            if infos:
                ip = infos[0][4][0]
                return socket.create_connection((ip, port), timeout, self.source_address)
        except Exception as exc:
            logger.debug("IPv4 getaddrinfo failed for %s: %s", host, exc)
        return super()._get_socket(host, port, timeout)


class IPv4SMTP_SSL(smtplib.SMTP_SSL):
    """SMTP_SSL client forcing IPv4 address resolution to prevent [Errno 101] Network is unreachable in cloud containers."""
    def _get_socket(self, host, port, timeout):
        try:
            infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
            if infos:
                ip = infos[0][4][0]
                sock = socket.create_connection((ip, port), timeout, self.source_address)
                server_hostname = self.host if self.host else host
                return self.context.wrap_socket(sock, server_hostname=server_hostname)
        except Exception as exc:
            logger.debug("IPv4 SSL getaddrinfo failed for %s: %s", host, exc)
        return super()._get_socket(host, port, timeout)


_smtp_blocked_until = 0.0


def _get_smtp_config():
    resend_key = os.getenv("RESEND_API_KEY", "").strip()
    brevo_key = os.getenv("BREVO_API_KEY", "").strip()
    host = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER", "smtp.gmail.com")
    user = os.getenv("SMTP_USER") or os.getenv("SMTP_EMAIL", "")
    password = os.getenv("SMTP_PASSWORD", "")
    port = int(os.getenv("SMTP_PORT", "465"))  # Default to 465 SSL for high reliability on cloud containers
    sender = os.getenv("ALERT_FROM_EMAIL") or user or "Landslide Guardian <onboarding@resend.dev>"
    return host, user, password, port, sender, resend_key, brevo_key

def _smtp_configured():
    host, user, password, _, _, resend_key, brevo_key = _get_smtp_config()
    return bool(resend_key or brevo_key or (host and user and password))


def _send_via_brevo(api_key: str, sender: str, recipient: str, subject: str, body: str) -> dict:
    try:
        sender_email = sender if ("@" in sender and "<" not in sender) else "sahaanuska99@gmail.com"
        sender_name = "Landslide Guardian"
        if "<" in sender and ">" in sender:
            sender_name = sender.split("<")[0].strip()
            sender_email = sender.split("<")[1].split(">")[0].strip()
            
        res = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "sender": {"name": sender_name, "email": sender_email},
                "to": [{"email": recipient}],
                "subject": subject,
                "textContent": body,
            },
            timeout=10,
        )
        if res.status_code in (200, 201):
            data = res.json()
            print(f"[BREVO SUCCESS] Email sent via HTTP API to {recipient} (id: {data.get('messageId')})")
            return {"status": "SENT", "recipient": recipient, "provider": "brevo", "id": data.get("messageId")}
        else:
            err = res.text
            print(f"[BREVO ERROR] Status {res.status_code}: {err}")
            return {"status": "FAILED", "recipient": recipient, "error": f"Brevo API error: {err}"}
    except Exception as exc:
        return {"status": "FAILED", "recipient": recipient, "error": f"Brevo HTTP request failed: {exc}"}


def _send_via_resend(api_key: str, sender: str, recipient: str, subject: str, body: str) -> dict:
    try:
        from_email = sender if ("@" in sender and not sender.endswith("@gmail.com")) else "Landslide Guardian <onboarding@resend.dev>"
        res = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": from_email,
                "to": [recipient],
                "subject": subject,
                "text": body,
            },
            timeout=12,
        )
        if res.status_code in (200, 201):
            data = res.json()
            print(f"[RESEND SUCCESS] Email sent via HTTP API to {recipient} (id: {data.get('id')})")
            return {"status": "SENT", "recipient": recipient, "provider": "resend", "id": data.get("id")}
        else:
            err = res.text
            print(f"[RESEND ERROR] Status {res.status_code}: {err}")
            return {"status": "FAILED", "recipient": recipient, "error": f"Resend API error: {err}"}
    except Exception as exc:
        return {"status": "FAILED", "recipient": recipient, "error": f"Resend HTTP request failed: {exc}"}


def _send(recipient: str, subject: str, body: str) -> dict:
    global _smtp_blocked_until
    import time
    host, user, password, port, sender, resend_key, brevo_key = _get_smtp_config()

    target_recipient = recipient.strip()

    # 1. Cloud HTTP API: Brevo (No sandbox restriction — delivers to ANY recipient over HTTPS)
    if brevo_key:
        brevo_res = _send_via_brevo(brevo_key, sender, target_recipient, subject, body)
        if brevo_res["status"] == "SENT":
            return brevo_res

    # 2. Cloud HTTP API: Resend (Port 443 — NEVER blocked by Railway)
    if resend_key:
        resend_res = _send_via_resend(resend_key, sender, target_recipient, subject, body)
        if resend_res["status"] == "SENT":
            return resend_res

    # 3. Check if SMTP credentials exist
    if not (user and password):
        print(f"[SMTP WARNING] Credentials missing. Simulated send to: {target_recipient}")
        return {
            "status": "NOT_CONFIGURED",
            "recipient": target_recipient,
            "message": "SMTP credentials (SMTP_USER/SMTP_PASSWORD) or RESEND_API_KEY/BREVO_API_KEY are not configured in environment."
        }

    # 4. Check if raw SMTP ports are currently blocked by host network firewall
    if time.time() < _smtp_blocked_until:
        return {
            "status": "NETWORK_BLOCKED",
            "recipient": target_recipient,
            "error": "Outbound raw SMTP ports (465/587) are firewalled by the container platform. Set RESEND_API_KEY or BREVO_API_KEY in Railway Variables for direct email delivery."
        }

    clean_password = password.strip().replace(" ", "")
    clean_user = user.strip()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Landslide Guardian <{sender.strip()}>"
    msg["To"] = target_recipient
    msg.set_content(body)

    # Establish priority connection methods: try primary port, then fallback port if network/socket fails
    connection_attempts = []
    if port == 587:
        connection_attempts.append(("STARTTLS", 587))
        connection_attempts.append(("SSL", 465))
    else:
        # Default to SSL port 465 first, then fallback to 587 STARTTLS
        connection_attempts.append(("SSL", 465))
        connection_attempts.append(("STARTTLS", 587))

    last_error = None
    last_port_used = port

    for method, p in connection_attempts:
        last_port_used = p
        try:
            if method == "SSL":
                with IPv4SMTP_SSL(host, p, timeout=4) as server:
                    server.login(clean_user, clean_password)
                    server.send_message(msg)
            else:
                with IPv4SMTP(host, p, timeout=4) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(clean_user, clean_password)
                    server.send_message(msg)

            print(f"[SMTP SUCCESS] Email successfully sent to -> {target_recipient} (via {method} port {p})")
            return {
                "status": "SENT",
                "recipient": target_recipient,
                "port_used": p,
                "method_used": method
            }

        except smtplib.SMTPAuthenticationError as auth_err:
            err_msg = (
                f"SMTP Authentication failed for '{clean_user}' (code: {auth_err.smtp_code}). "
                "CRITICAL: If you recently changed your Google Account password, Google automatically invalidated all previous App Passwords. "
                "You MUST create a NEW 16-character App Password at: https://myaccount.google.com/apppasswords "
                "(Google Account -> Security -> 2-Step Verification -> App Passwords). "
                "Then copy the new 16-character code into Railway Variables as SMTP_PASSWORD (do not use your regular Gmail password)."
            )
            print(f"[SMTP AUTH ERROR] {err_msg}")
            logger.warning(err_msg)
            return {
                "status": "AUTH_FAILED",
                "recipient": target_recipient,
                "error": err_msg,
                "guide_url": "https://myaccount.google.com/apppasswords"
            }

        except (OSError, socket.error, smtplib.SMTPConnectError) as net_err:
            last_error = net_err
            print(f"[SMTP WARNING] Port {p} ({method}) network error: {net_err}. Attempting fallback port...")
            continue
        except Exception as exc:
            last_error = exc
            print(f"[SMTP ERROR] Failed sending on port {p} to {target_recipient}: {exc}")
            break

    final_err_msg = f"Network connection failed on ports 465 and 587: {last_error}"
    if isinstance(last_error, (OSError, socket.error)):
        # Host network is blocking raw email socket connections (standard on cloud containers like Railway)
        _smtp_blocked_until = time.time() + 300
    logger.warning("Email dispatch failed to %s: %s", target_recipient, final_err_msg)
    return {
        "status": "FAILED",
        "recipient": target_recipient,
        "error": str(last_error) if last_error else "Connection failed",
        "detail": final_err_msg
    }


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


def send_alert_email(
    recipient: str,
    location: str,
    message: str,
    risk_score=None,
    risk_level=None,
    lang: str = "en",
):
    try:
        from .multilingual import generate_multilingual_alert
        alert_data = generate_multilingual_alert(
            location=location,
            risk_level=risk_level or "HIGH",
            risk_score=risk_score,
            custom_msg=message,
            lang=lang,
        )
        subject = alert_data["subject"]
        body = alert_data["body"]
    except Exception as exc:
        logger.warning("Multilingual alert generation failed, using standard template: %s", exc)
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

def dispatch_email_sos(
    location: str,
    users: list,
    custom_msg: str = None,
    risk_score=None,
    risk_level=None,
    lang: str = None,
):
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
        user_lang = lang or (user.get("language", "en") if isinstance(user, dict) else "en")
        result = send_alert_email(email, location, message, risk_score, risk_level, lang=user_lang)
        logs.append({
            "name": name,
            "email": email,
            "language": user_lang,
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