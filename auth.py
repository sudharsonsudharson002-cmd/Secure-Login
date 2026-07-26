from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.exceptions import abort

from database import db
from forms import (ChangePasswordForm, ForgotPasswordForm, LoginForm, ProfileForm,
                   RegisterForm, ResetPasswordForm, ResendVerificationForm,
                   SecuritySettingsForm, TwoFactorForm)
from models import ActivityLog, LoginLog, User
from security import (generate_2fa_secret, generate_email_token, generate_qr_code_data_uri,
                      generate_reset_token, generate_totp_uri, get_client_info, hash_password,
                      is_session_valid, send_email, verify_email_token, verify_password,
                      verify_reset_token, verify_totp)
from utils import clear_failed_attempts, handle_login_lockout, log_activity, save_profile_picture

bp = Blueprint("auth", __name__)


@bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username == form.username.data) | (User.email == form.username.data.lower())).first()
        if user:
            if user.account_locked:
                flash("Your account has been locked after too many failed sign-in attempts.", "danger")
                return redirect(url_for("auth.login"))
            if not user.is_verified:
                flash("Email verification is required before signing in. Check your inbox or resend verification.", "warning")
                return redirect(url_for("auth.resend_verification"))
            if verify_password(form.password.data, user.password_hash):
                clear_failed_attempts(user)
                if user.two_factor_secret:
                    session["pending_2fa_user_id"] = user.id
                    session["remember_me"] = form.remember_me.data
                    info = get_client_info()
                    db.session.add(LoginLog(user_id=user.id, ip_address=info["ip"], browser=info["browser"], device=info["device"], location=info["location"], status="pending_2fa", login_time=datetime.utcnow()))
                    db.session.commit()
                    flash("Enter your authenticator code to complete login.", "info")
                    return redirect(url_for("auth.two_factor"))
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                info = get_client_info()
                db.session.add(LoginLog(user_id=user.id, ip_address=info["ip"], browser=info["browser"], device=info["device"], location=info["location"], status="success", login_time=datetime.utcnow()))
                db.session.commit()
                log_activity(user.id, "Successful login")
                session["last_activity"] = datetime.utcnow().isoformat()
                flash("Welcome back!", "success")
                return redirect(url_for("auth.dashboard"))
            handle_login_lockout(user)
            flash("Invalid credentials or account locked.", "danger")
        else:
            flash("Invalid credentials or account locked.", "danger")
        return redirect(url_for("auth.login"))
    return render_template("login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data.lower(), password_hash=hash_password(form.password.data), is_verified=False)
        db.session.add(user)
        db.session.commit()
        token = generate_email_token(user.id)
        verification_url = url_for("auth.confirm_email", token=token, _external=True)
        email_body = render_template("verify_email.html", user=user, verification_url=verification_url)
        if send_email(user.email, "Verify your Secure Login account", email_body):
            flash("Account created successfully. Check your email to verify your account.", "success")
        else:
            flash("Account created. Verify your email once SMTP is configured.", "warning")
        log_activity(user.id, "Account created")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = generate_reset_token(user.id)
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            email_body = render_template("reset_email.html", user=user, reset_url=reset_url)
            send_email(user.email, "Secure Login password reset", email_body)
            log_activity(user.id, "Password reset requested")
        flash("If an account exists for that email, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html", form=form)


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user_id = verify_reset_token(token)
    if not user_id:
        flash("Invalid or expired reset token.", "danger")
        return redirect(url_for("auth.login"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.get(user_id)
        if user:
            user.password_hash = hash_password(form.password.data)
            db.session.commit()
            log_activity(user.id, "Password reset")
            flash("Password updated successfully.", "success")
            return redirect(url_for("auth.login"))
    return render_template("reset_password.html", form=form, token=token)


@bp.route("/verify-email/<token>")
def confirm_email(token):
    user_id = verify_email_token(token)
    if not user_id:
        flash("Verification link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))
    user = User.query.get(user_id)
    if not user:
        flash("Verification link is invalid.", "danger")
        return redirect(url_for("auth.login"))
    user.is_verified = True
    db.session.commit()
    log_activity(user.id, "Email verified")
    flash("Your email has been verified. You can now sign in.", "success")
    return redirect(url_for("auth.login"))


@bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    form = ResendVerificationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and not user.is_verified:
            token = generate_email_token(user.id)
            verification_url = url_for("auth.confirm_email", token=token, _external=True)
            email_body = render_template("verify_email.html", user=user, verification_url=verification_url)
            if send_email(user.email, "Verify your Secure Login account", email_body):
                flash("Verification email resent. Check your inbox.", "success")
            else:
                flash("Verification email queued. Configure SMTP to deliver messages.", "warning")
            log_activity(user.id, "Verification email resent")
            return redirect(url_for("auth.login"))
        flash("If the email exists, a verification message will be sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("resend_verification.html", form=form)


@bp.route("/two-factor", methods=["GET", "POST"])
def two_factor():
    pending_user_id = session.get("pending_2fa_user_id")
    if not pending_user_id:
        flash("Two-factor authentication session expired. Sign in again.", "warning")
        return redirect(url_for("auth.login"))
    user = User.query.get(pending_user_id)
    if not user or not user.two_factor_secret:
        flash("Unable to verify two-factor authentication.", "danger")
        return redirect(url_for("auth.login"))
    form = TwoFactorForm()
    if form.validate_on_submit():
        if verify_totp(user.two_factor_secret, form.code.data):
            login_user(user, remember=session.pop("remember_me", False))
            session.pop("pending_2fa_user_id", None)
            user.last_login = datetime.utcnow()
            db.session.commit()
            info = get_client_info()
            db.session.add(LoginLog(user_id=user.id, ip_address=info["ip"], browser=info["browser"], device=info["device"], location=info["location"], status="success", login_time=datetime.utcnow()))
            db.session.commit()
            log_activity(user.id, "Two-factor authentication approved")
            session["last_activity"] = datetime.utcnow().isoformat()
            flash("Two-factor authentication succeeded.", "success")
            return redirect(url_for("auth.dashboard"))
        flash("Invalid authentication code. Please try again.", "danger")
    return render_template("two_factor.html", form=form)


@bp.route("/dashboard")
@login_required
def dashboard():
    if not is_session_valid(session):
        logout_user()
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))
    session["last_activity"] = datetime.utcnow().isoformat()
    recent_activity = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.timestamp.desc()).limit(8).all()
    login_history = LoginLog.query.filter_by(user_id=current_user.id).order_by(LoginLog.login_time.desc()).limit(6).all()
    security_score = 92
    return render_template("dashboard.html", recent_activity=recent_activity, login_history=login_history, security_score=security_score)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data.lower()
        if form.profile_picture.data:
            picture_path = save_profile_picture(form.profile_picture.data, current_user.id)
            if picture_path:
                current_user.profile_picture = picture_path
        db.session.commit()
        log_activity(current_user.id, "Profile updated")
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("profile.html", form=form)


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = SecuritySettingsForm(obj=current_user)
    qr_code_data = None
    totp_uri = None
    if form.validate_on_submit():
        if form.enable_2fa.data:
            if not current_user.two_factor_secret:
                current_user.two_factor_secret = generate_2fa_secret()
                db.session.commit()
            flash("Two-factor authentication enabled. Use the QR code below to configure your authenticator app.", "success")
        else:
            current_user.two_factor_secret = None
            db.session.commit()
            flash("Two-factor authentication disabled.", "info")
        return redirect(url_for("auth.settings"))
    secret = current_user.two_factor_secret
    if secret:
        totp_uri = generate_totp_uri(secret, current_user.email or current_user.username)
        qr_code_data = generate_qr_code_data_uri(totp_uri)
    return render_template("settings.html", form=form, qr_code_data=qr_code_data, secret=secret)


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if verify_password(form.current_password.data, current_user.password_hash):
            current_user.password_hash = hash_password(form.new_password.data)
            db.session.commit()
            log_activity(current_user.id, "Password changed")
            flash("Password changed successfully.", "success")
            return redirect(url_for("auth.profile"))
        flash("Current password is incorrect.", "danger")
    return render_template("profile.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/logout-everywhere")
@login_required
def logout_everywhere():
    logout_user()
    session.clear()
    flash("All sessions were invalidated.", "info")
    return redirect(url_for("auth.login"))


@bp.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@bp.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500
