"""Minimal Flask app for validating an idea with a poll + email signup.

This file intentionally keeps logic straightforward and heavily commented,
so it is easy to copy and adapt for future ideas.

Environment variables (set these in production):
  SECRET_KEY      Random string that signs the session cookie. CSRF protection
                  depends on it; set it so sessions survive restarts/instances.
  ADMIN_USERNAME  HTTP Basic Auth user for /admin/export.
  ADMIN_PASSWORD  HTTP Basic Auth password for /admin/export.
  FLASK_DEBUG     "1" to enable the debug server locally. NEVER set in production
                  (the debug console allows remote code execution).
  TRUST_PROXY     "1" when running behind a reverse proxy (Render/Railway/Nginx)
                  so the real client IP is read from X-Forwarded-For.
  SECURE_COOKIES  "1" to mark the session cookie Secure (HTTPS deployments).
  HOST / PORT     Bind address for the built-in dev server (defaults 127.0.0.1:5000).
"""

from __future__ import annotations

import csv
import io
import logging
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

import config

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"

# Basic email regex (simple and beginner-friendly, not overly strict).
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Console logging helps you see successful signups in development and production logs.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Security configuration -------------------------------------------------

# The session cookie is signed with SECRET_KEY, and CSRF protection relies on it.
# A missing key in production would silently rotate on restart and invalidate
# every session, so we generate a temporary one but warn loudly.
_secret_key = os.environ.get("SECRET_KEY")
if not _secret_key:
    _secret_key = secrets.token_hex(32)
    logger.warning(
        "SECRET_KEY is not set; generated a temporary key. "
        "Set SECRET_KEY in production so sessions and CSRF tokens stay valid."
    )

app.config.update(
    SECRET_KEY=_secret_key,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SECURE_COOKIES", "0") == "1",
)

# Behind a reverse proxy the real client IP arrives in X-Forwarded-For. Only trust
# it when a proxy is actually present, otherwise clients could spoof that header to
# dodge the rate limiter. Enable with TRUST_PROXY=1 on Render/Railway/Nginx.
if os.environ.get("TRUST_PROXY", "0") == "1":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[method-assign]

# Rate limiting protects the email list from scripted flooding. We deliberately
# limit only the mutating/sensitive endpoints so public page views (and any
# virality) stay unthrottled. In-memory storage is fine for a single instance;
# point storage_uri at Redis if you scale to multiple workers/instances.
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri="memory://",
)


def get_db_connection() -> sqlite3.Connection:
    """Create a new SQLite connection.

    We use sqlite3.Row so rows can be accessed like dictionaries
    (e.g., row["email"]) which is easier to read.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create the submissions table if it does not already exist."""
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                poll_answer TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def normalize_text(value: str) -> str:
    """Trim whitespace from user input.

    Jinja auto-escapes template output by default, so we keep stored values readable
    and only normalize whitespace here.
    """
    return value.strip()


def is_valid_email(email: str) -> bool:
    """Return True if email format passes our basic regex check."""
    return bool(EMAIL_REGEX.match(email))


def csv_safe(value: str) -> str:
    """Prevent CSV formula injection in exported data.

    If a value starts with spreadsheet formula characters, prefix a single quote.
    """
    if value and value[0] in ("=", "+", "-", "@"):
        return f"'{value}"
    return value


def get_csrf_token() -> str:
    """Return the per-session CSRF token, creating one if needed."""
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def csrf_is_valid() -> bool:
    """Constant-time comparison of the submitted token against the session token."""
    submitted = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    return bool(expected) and secrets.compare_digest(submitted, expected)


@app.context_processor
def inject_csrf_token() -> dict[str, str]:
    """Expose {{ csrf_token }} to every template."""
    return {"csrf_token": get_csrf_token()}


def require_admin_auth(view: Callable[..., Any]) -> Callable[..., Any]:
    """Protect a view with HTTP Basic Auth from ADMIN_USERNAME / ADMIN_PASSWORD.

    Fails closed: if credentials are not configured, access is denied so an
    incomplete deployment can never expose the email list.
    """

    @wraps(view)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        expected_user = os.environ.get("ADMIN_USERNAME")
        expected_password = os.environ.get("ADMIN_PASSWORD")
        if not expected_user or not expected_password:
            logger.error(
                "Admin export blocked: set ADMIN_USERNAME and ADMIN_PASSWORD to enable it."
            )
            abort(503, description="Admin export is not configured.")

        auth = request.authorization
        provided_user = auth.username if auth and auth.username else ""
        provided_password = auth.password if auth and auth.password else ""
        # Compare both fields (always, to avoid leaking which one was wrong via timing).
        user_ok = secrets.compare_digest(provided_user, expected_user)
        password_ok = secrets.compare_digest(provided_password, expected_password)
        if not (user_ok and password_ok):
            return Response(
                "Authentication required.",
                401,
                {"WWW-Authenticate": 'Basic realm="Admin export"'},
            )
        return view(*args, **kwargs)

    return wrapper


def page_context(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Central place for template values from config.py.

    This keeps templates dynamic and makes project reuse simple.
    """
    context: dict[str, Any] = {
        "site_title": config.SITE_TITLE,
        "headline": config.HEADLINE,
        "description": config.DESCRIPTION,
        "poll_question": config.POLL_QUESTION,
        "poll_options": config.POLL_OPTIONS,
    }
    if extra:
        context.update(extra)
    return context


@app.route("/")
def index() -> str:
    """Landing page route."""
    return render_template("index.html", **page_context())


@app.route("/submit", methods=["POST"])
@limiter.limit("5 per minute; 50 per day")
def submit() -> Response | tuple[str, int] | str:
    """Handle form submission with validation and duplicate prevention."""
    # Reject forged/expired submissions before doing any work.
    if not csrf_is_valid():
        return (
            render_template(
                "index.html",
                **page_context(
                    {"error": "Your session expired. Please reload the page and try again."}
                ),
            ),
            400,
        )

    raw_email = request.form.get("email", "")
    raw_poll_answer = request.form.get("poll_answer", "")

    email = normalize_text(raw_email).lower()
    poll_answer = normalize_text(raw_poll_answer)

    # Preserve entered values if there is an error.
    form_values = {"email": email, "selected_poll_answer": poll_answer}

    if not email or not poll_answer:
        return render_template(
            "index.html",
            **page_context(
                {
                    "error": "Please enter your email and choose one poll option.",
                    **form_values,
                }
            ),
        )

    if not is_valid_email(email):
        return render_template(
            "index.html",
            **page_context(
                {
                    "error": "Please enter a valid email address.",
                    **form_values,
                }
            ),
        )

    if poll_answer not in config.POLL_OPTIONS:
        return render_template(
            "index.html",
            **page_context(
                {
                    "error": "Please select a valid poll option.",
                    **form_values,
                }
            ),
        )

    created_at = datetime.now(timezone.utc).isoformat()

    try:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO submissions (email, poll_answer, created_at)
                VALUES (?, ?, ?)
                """,
                (email, poll_answer, created_at),
            )
            connection.commit()
    except sqlite3.IntegrityError:
        return render_template(
            "index.html",
            **page_context(
                {
                    "error": "This email is already registered. Thanks for your interest!",
                    **form_values,
                }
            ),
        )

    logger.info("New signup: email=%s poll_answer=%s at=%s", email, poll_answer, created_at)
    return redirect(url_for("thank_you"))


@app.route("/thank-you")
def thank_you() -> str:
    """Simple confirmation page after successful submission."""
    return render_template("thank_you.html", **page_context())


@app.route("/admin/export")
@limiter.limit("20 per hour")
@require_admin_auth
def admin_export() -> Response:
    """Download all submissions as CSV (protected by HTTP Basic Auth)."""
    with get_db_connection() as connection:
        submissions = connection.execute(
            "SELECT id, email, poll_answer, created_at FROM submissions ORDER BY created_at DESC"
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "email", "poll_answer", "created_at"])

    for row in submissions:
        writer.writerow(
            [
                row["id"],
                csv_safe(row["email"]),
                csv_safe(row["poll_answer"]),
                csv_safe(row["created_at"]),
            ]
        )

    csv_data = output.getvalue()

    # Bonus: include submission count in headers for a quick admin success indicator.
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=submissions.csv",
            "X-Total-Submissions": str(len(submissions)),
        },
    )


@app.errorhandler(429)
def handle_rate_limit(_error: Any) -> tuple[str, int]:
    """Friendly response when a client trips the rate limiter."""
    return (
        render_template(
            "index.html",
            **page_context(
                {"error": "Too many attempts. Please wait a moment and try again."}
            ),
        ),
        429,
    )


@app.after_request
def set_security_headers(response: Response) -> Response:
    """Conservative security headers applied to every response."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


if __name__ == "__main__":
    init_db()
    # Debug is OFF unless explicitly enabled. The debug console exposes an
    # interactive shell (remote code execution) and must never run in production.
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=debug)
else:
    # Ensures database is ready when run by production servers (waitress, gunicorn).
    init_db()
