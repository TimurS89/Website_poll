# Idea Validation Landing Page (Flask + SQLite)

A clean, minimal, reusable landing page to validate product ideas by collecting:
- Email
- Poll answer (3–4 options)
- Timestamp

## Project Structure

```text
idea_validator/
│
├── app.py
├── config.py
├── requirements.txt
├── database.db (auto-created)
│
├── templates/
│   ├── index.html
│   └── thank_you.html
│
└── static/
    └── style.css
```

## 1) Create and activate a virtual environment

From repository root:

```bash
cd idea_validator
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
cd idea_validator
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 2) Install dependencies

```bash
pip install -r requirements.txt
```

## 3) Run locally

```bash
python app.py
```

Open: `http://127.0.0.1:5000`

The development server runs with **debug OFF by default**. To enable Flask's
auto-reloading debug server while developing (never in production), set
`FLASK_DEBUG=1`:

```bash
# macOS / Linux
FLASK_DEBUG=1 python app.py
```

```powershell
# Windows PowerShell
$env:FLASK_DEBUG = "1"; python app.py
```

## Configuration (environment variables)

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Signs the session cookie; CSRF protection depends on it. Set a long random value in production so sessions survive restarts. |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | HTTP Basic Auth credentials for `/admin/export`. **If unset, the export endpoint is disabled (returns 503)** so the email list is never exposed by accident. |
| `FLASK_DEBUG` | `1` enables the dev debug server. Never set in production. |
| `TRUST_PROXY` | `1` when running behind a reverse proxy (Render/Railway/Nginx) so the real client IP is read from `X-Forwarded-For` for rate limiting. |
| `SECURE_COOKIES` | `1` to mark the session cookie `Secure` (HTTPS deployments). |
| `HOST` / `PORT` | Bind address/port for the dev server (default `127.0.0.1:5000`). |

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Run in production (Windows & Linux)

Do **not** use `python app.py` in production — that launches the debug server.
Serve the app with [waitress](https://github.com/Pylons/waitress), a pure-Python
WSGI server that runs on both Windows and Linux:

```bash
# macOS / Linux
export SECRET_KEY="<your-random-key>"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="<your-password>"
export TRUST_PROXY=1
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

```powershell
# Windows PowerShell
$env:SECRET_KEY = "<your-random-key>"
$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD = "<your-password>"
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

## Routes

- `/` → landing page (Open Graph / Twitter share cards in the `<head>`)
- `/submit` → POST form handler (CSRF-protected, rate limited)
- `/thank-you` → success page with live poll results, social share buttons, and an optional community link
- `/og-image.png` → 1200×630 social-share image generated on the fly from `config.py`
- `/admin/export` → download CSV of submissions (**requires HTTP Basic Auth**; disabled until `ADMIN_USERNAME`/`ADMIN_PASSWORD` are set)

## Reuse for another idea

Duplicate `idea_validator/` and edit only `config.py`:
- `SITE_TITLE`
- `HEADLINE`
- `DESCRIPTION`
- `POLL_QUESTION`
- `POLL_OPTIONS`
- `COMMUNITY_URL` / `COMMUNITY_LABEL` (optional button on the thank-you page; leave the URL blank to hide it)
- `SHARE_MESSAGE` (text pre-filled in social share links)
- `PARTICIPANT_BASELINE` (social-proof floor; the counter shows e.g. "1,000+" until real sign-ups overtake it, then the true live number — set to `0` to show only real counts)
- `RESULTS_MIN_VOTES` (poll result bars appear only after this many real votes)

Everything in the HTML and the generated share image reads from these values dynamically.

## Simple deployment

### Render (Web Service)

- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
waitress-serve --host=0.0.0.0 --port=$PORT app:app
```

- Set root directory to `idea_validator`.
- In the dashboard, set env vars: `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `TRUST_PROXY=1`.

### Railway

- Deploy from repo
- Set root directory to `idea_validator`
- Start command:

```bash
waitress-serve --host=0.0.0.0 --port=$PORT app:app
```

- Set env vars: `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `TRUST_PROXY=1`.

## Notes

- SQLite table `submissions` is auto-created if missing.
- `database.db` is intentionally not committed to git (SQLite is a binary file); it is created automatically on first run.
- Duplicate emails are blocked (`email` is unique). Re-submitting an existing email returns the same thank-you page rather than revealing that it is already registered (prevents email enumeration).
- Basic email regex validation is included.
- Input is normalized and validated server-side.
- New signups are logged to console with a hashed email fingerprint; raw email addresses are never written to logs.
- The signup form is CSRF-protected with a per-session token.
- `/submit` is rate limited (5/min, 50/day per IP); `/admin/export` is rate limited (20/hour) and requires HTTP Basic Auth.
- The `/og-image.png` share image is rendered once and cached in memory, so the public endpoint does no per-request image work.
- Security headers are sent on every response: `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Strict-Transport-Security` (HSTS, only over HTTPS).
- The debug server is disabled unless `FLASK_DEBUG=1`, so production never exposes the interactive debugger.
- The thank-you page reveals live poll results (the visitor's own pick is highlighted) and offers X/LinkedIn/WhatsApp/Telegram share links.
- A social-proof counter on both pages uses the floor model `max(PARTICIPANT_BASELINE, real signups)`: it reads "1,000+" until real sign-ups overtake the baseline, then switches to the true number automatically. Poll percentages are always computed from real votes only (the seeded number never feeds them), and the raw vote count is not displayed, so the two never contradict each other.
- First-touch attribution (`utm_source`, `utm_medium`, `utm_campaign`, and the `referrer` origin — scheme + host only, no path or query string) is captured per visitor and included in the CSV export. Share links carry UTM tags so returning traffic is attributed to its platform.
- Existing databases are migrated automatically: the attribution columns are added on startup if missing.

## Git branch note

All project files are committed in git in this repository history.
If you need this on `main`, merge or cherry-pick the latest work branch commit.
