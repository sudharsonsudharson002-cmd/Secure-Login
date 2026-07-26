import base64
import io
import os
import secrets
import smtplib
import string
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional

import pyotp
import qrcode
from flask import current_app, request, url_for
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from itsdangerous import URLSafeTimedSerializer

bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"))


def init_security(app) -> None:
    global serializer
    serializer = URLSafeTimedSerializer(app.secret_key)


def hash_password(password: str) -> str:
    return bcrypt.generate_password_hash(password).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.check_password_hash(password_hash, password)


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    mail_server = os.getenv("MAIL_SERVER")
    mail_port = int(os.getenv("MAIL_PORT", "587"))
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    mail_use_tls = os.getenv("MAIL_USE_TLS", "True").lower() in {"true", "1", "yes"}
    mail_use_ssl = os.getenv("MAIL_USE_SSL", "False").lower() in {"true", "1", "yes"}
    from_address = os.getenv("MAIL_DEFAULT_SENDER", f"no-reply@{os.getenv('MAIL_DOMAIN', 'securelogin.local')}")

    if not mail_server:
        current_app.logger.warning("Email not sent because MAIL_SERVER is not configured.")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = to_email
    message.set_content("Please view this message in an HTML-compatible email client.")
    message.add_alternative(html_body, subtype="html")

    try:
        if mail_use_ssl:
            smtp = smtplib.SMTP_SSL(mail_server, mail_port, timeout=10)
        else:
            smtp = smtplib.SMTP(mail_server, mail_port, timeout=10)
            if mail_use_tls:
                smtp.starttls()
        if mail_username and mail_password:
            smtp.login(mail_username, mail_password)
        smtp.send_message(message)
        smtp.quit()
        current_app.logger.info(f"Sent email to {to_email}")
        return True
    except Exception as exc:
        current_app.logger.exception("Unable to send email: %s", exc)
        return False


def generate_reset_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id}, salt="password-reset")


def verify_reset_token(token: str, max_age: int = 1800) -> Optional[int]:
    try:
        data = serializer.loads(token, salt="password-reset", max_age=max_age)
        return data.get("user_id")
    except Exception:
        return None


def generate_email_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id}, salt="email-confirm")


def verify_email_token(token: str, max_age: int = 86400) -> Optional[int]:
    try:
        data = serializer.loads(token, salt="email-confirm", max_age=max_age)
        return data.get("user_id")
    except Exception:
        return None


def generate_2fa_secret() -> str:
    return pyotp.random_base32()


def generate_totp_uri(secret: str, username: str, issuer: str = "Secure Login") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_qr_code(data: str, output_path: str) -> None:
    img = qrcode.make(data)
    img.save(output_path)


def generate_qr_code_data_uri(data: str) -> str:
    img = qrcode.make(data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def password_strength(password: str) -> dict:
    score = 0
    feedback = []
    if len(password) >= 12:
        score += 1
    else:
        feedback.append("Use at least 12 characters")
    if any(char.isupper() for char in password):
        score += 1
    else:
        feedback.append("Include uppercase letters")
    if any(char.islower() for char in password):
        score += 1
    else:
        feedback.append("Include lowercase letters")
    if any(char.isdigit() for char in password):
        score += 1
    else:
        feedback.append("Include numbers")
    if any(char in string.punctuation for char in password):
        score += 1
    else:
        feedback.append("Include a special character")
    return {"score": score, "feedback": feedback}


def get_client_info() -> dict:
    user_agent = request.headers.get("User-Agent", "Unknown")
    browser = "Unknown"
    device = "Unknown"
    if "Chrome" in user_agent:
        browser = "Chrome"
    elif "Firefox" in user_agent:
        browser = "Firefox"
    elif "Safari" in user_agent:
        browser = "Safari"
    elif "Edge" in user_agent:
        browser = "Edge"
    if "Mobile" in user_agent:
        device = "Mobile"
    elif "Tablet" in user_agent:
        device = "Tablet"
    else:
        device = "Desktop"
    return {"ip": request.remote_addr or "127.0.0.1", "browser": browser, "device": device, "location": "Unknown"}


def is_session_valid(session: dict) -> bool:
    if not session.get("last_activity"):
        return False
    last_activity = datetime.fromisoformat(session["last_activity"])
    return datetime.now(timezone.utc) - last_activity < timedelta(minutes=30)
