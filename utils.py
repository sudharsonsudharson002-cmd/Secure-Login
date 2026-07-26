import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import flash, redirect, request, url_for
from PIL import Image

from models import ActivityLog
from database import db


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "gif", "webp"}


def save_profile_picture(file_storage, user_id: int) -> str:
    if not file_storage or not hasattr(file_storage, "filename"):
        return ""
    if not allowed_file(file_storage.filename):
        return ""
    filename = f"{user_id}_{secrets.token_hex(8)}_{Path(file_storage.filename).name}"
    upload_path = Path("static/images") / filename
    image = Image.open(file_storage)
    image.thumbnail((300, 300))
    image.save(upload_path)
    return f"/static/images/{filename}"


def log_activity(user_id: int, activity: str) -> None:
    db.session.add(ActivityLog(user_id=user_id, activity=activity, timestamp=datetime.utcnow()))
    db.session.commit()


def handle_login_lockout(user) -> None:
    user.failed_attempts += 1
    if user.failed_attempts >= 5:
        user.account_locked = True
    db.session.commit()


def clear_failed_attempts(user) -> None:
    user.failed_attempts = 0
    db.session.commit()


def is_safe_redirect(target: str | None) -> bool:
    if not target:
        return False
    return target.startswith("/") and not target.startswith("//")
