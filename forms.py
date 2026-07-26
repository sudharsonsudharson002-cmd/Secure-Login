from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, EmailField, PasswordField, StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from models import User


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)], render_kw={"placeholder": "username"})
    email = EmailField("Email", validators=[DataRequired(), Email(message="Enter a valid email address")], render_kw={"placeholder": "you@gmail.com"})
    password = PasswordField("Password", validators=[DataRequired(), Length(min=12)], render_kw={"placeholder": "Create a strong password"})
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")], render_kw={"placeholder": "Confirm your password"})
    submit = SubmitField("Create Account")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already exists.")

    def validate_email(self, field):
        email = field.data.strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValidationError("Enter a valid email address such as user@gmail.com.")
        if User.query.filter_by(email=email).first():
            raise ValidationError("Email already exists.")


class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(message="Enter a valid email address")], render_kw={"placeholder": "you@gmail.com"})
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired(), Length(min=12)], render_kw={"placeholder": "New strong password"})
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")], render_kw={"placeholder": "Confirm your password"})
    submit = SubmitField("Reset Password")


class ProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = EmailField("Email", validators=[DataRequired(), Email(message="Enter a valid email address")])
    profile_picture = FileField("Profile Picture", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"])])
    submit = SubmitField("Update Profile")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=12)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("new_password")])
    submit = SubmitField("Change Password")


class SecuritySettingsForm(FlaskForm):
    enable_2fa = BooleanField("Enable Two-Factor Authentication")
    submit = SubmitField("Save Security Settings")


class TwoFactorForm(FlaskForm):
    code = StringField("Authentication Code", validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField("Verify Code")


class ResendVerificationForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(message="Enter a valid email address")], render_kw={"placeholder": "you@gmail.com"})
    submit = SubmitField("Resend Verification Email")


