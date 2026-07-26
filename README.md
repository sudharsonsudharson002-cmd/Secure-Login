# Secure Login System

A production-ready cybersecurity web application built with Flask, SQLite, SQLAlchemy, Bootstrap 5, and modern security controls.

## Features

- Secure authentication with bcrypt password hashing
- Email verification workflow for new user activation
- CSRF protection and secure cookies
- Session management and remember-me support
- Account lockout after repeated failed attempts
- Password reset flow with secure token delivery
- Optional two-factor authentication with QR code setup
- Audit logging for login and activity events
- Responsive dark cyberpunk UI with animated visuals

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python app.py
   ```

## Folder Structure

- app.py: Application entry point
- auth.py: Authentication routes
- forms.py: Flask-WTF forms
- models.py: SQLAlchemy models
- security.py: Security helpers and token utilities
- templates/: HTML templates
- static/: CSS, JavaScript, and images

## Security Features

- SQL injection protection through SQLAlchemy parameterized queries
- XSS mitigation via Jinja2 autoescaping and secure templates
- CSRF tokens on forms
- Rate limiting and lockout controls
- Secure cookie configuration and session timeout logic

## Deployment

This project is ready for deployment to Render via the included Procfile and render.yaml.

## Email Configuration

To enable email-based verification and password reset delivery, set your SMTP settings in the environment using:

- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`
- `MAIL_USE_TLS`
- `MAIL_USE_SSL`

## License

This project is provided as a learning and demonstration project.
