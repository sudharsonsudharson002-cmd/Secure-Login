import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text

from config import Config
from database import db
from models import User
from security import init_security, limiter
from auth import bp as auth_bp


app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(auth_bp)

csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


db.init_app(app)
limiter.init_app(app)
init_security(app)


@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self';"
    return response


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


@app.before_request
def ensure_database():
    with app.app_context():
        db.create_all()


@app.context_processor
def inject_globals():
    return {"current_year": 2026}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
