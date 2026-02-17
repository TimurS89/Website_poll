"""Minimal Flask app for validating an idea with a poll + email signup.

This file intentionally keeps logic straightforward and heavily commented,
so it is easy to copy and adapt for future ideas.
"""

from __future__ import annotations

import csv
import io
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, Response, redirect, render_template, request, url_for

import config

# Some IDE consoles (e.g., PyCharm Python Console) execute code without __file__.
# In that case we fall back to the current working directory so imports still work.
if "__file__" in globals():
    BASE_DIR = Path(__file__).resolve().parent
else:
    # Helpful fallback for interactive consoles where __file__ is unavailable.
    cwd = Path.cwd()
    BASE_DIR = cwd / "idea_validator" if (cwd / "idea_validator").exists() else cwd

DB_PATH = BASE_DIR / "database.db"

# Basic email regex (simple and beginner-friendly, not overly strict).
EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = Flask(__name__)

# Console logging helps you see successful signups in development and production logs.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
def submit() -> Response | str:
    """Handle form submission with validation and duplicate prevention."""
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
def admin_export() -> Response:
    """Download all submissions as CSV."""
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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
else:
    # Ensures database is ready when run by production servers (gunicorn, etc.).
    init_db()
