# CLAUDE.md — AI Assistant Guide for Website_poll

This file documents the codebase structure, conventions, and workflows for AI
assistants working in this repository.

---

## Project Overview

A minimal, reusable Flask landing page that validates product ideas by
collecting an email address and a poll answer from visitors. Data is stored in
SQLite and can be exported as CSV by the project owner.

The project is intentionally simple and designed to be cloned and customised
quickly for different ideas by editing a single configuration file.

---

## Repository Layout

```
Website_poll/
├── CLAUDE.md                  ← this file
├── README.md                  ← human-facing setup guide
├── .gitignore
└── idea_validator/            ← entire application lives here
    ├── app.py                 ← Flask app (routes, DB logic, validation)
    ├── config.py              ← all user-facing text and poll options
    ├── requirements.txt       ← single dependency: Flask==3.0.3
    ├── database.db            ← SQLite file, auto-created, git-ignored
    ├── templates/
    │   ├── index.html         ← landing page / form
    │   └── thank_you.html     ← post-submission confirmation
    └── static/
        └── style.css          ← all styling (CSS custom properties)
```

---

## Technology Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Language   | Python 3.x                        |
| Web        | Flask 3.0.3 + Jinja2 templating   |
| Database   | SQLite 3 (stdlib `sqlite3`)       |
| Frontend   | HTML5, CSS3 (no JS framework)     |
| Deployment | Render or Railway (see README)    |

No JavaScript framework, no ORM, no external CSS library — keep it that way
unless the user explicitly asks to add something.

---

## Key Files to Understand

### `idea_validator/config.py`
The **only file that needs to be edited** when repurposing the project for a
new idea. Contains:

```python
SITE_TITLE    # <title> and page heading
HEADLINE      # large hero text
DESCRIPTION   # subheading paragraph
POLL_QUESTION # question shown above radio buttons
POLL_OPTIONS  # list[str] of radio button labels
```

All template values flow through `page_context()` in `app.py`; templates never
import config directly.

### `idea_validator/app.py`
Core application. Key sections:

- **`init_db()`** — creates the `submissions` table on startup (called in both
  `__main__` and module-level so gunicorn also triggers it).
- **`get_db_connection()`** — opens a new SQLite connection per request with
  `sqlite3.Row` factory for dict-style access.
- **`page_context(extra)`** — single function that builds the Jinja2 template
  context from `config.py`; add new config keys here and in `config.py`.
- **`normalize_text()`** — strips whitespace; all user input passes through it.
- **`is_valid_email()`** — basic regex `^[^\s@]+@[^\s@]+\.[^\s@]+$`; intentionally
  not strict.
- **`csv_safe()`** — prefixes `'` to values starting with `=+-@` to prevent
  formula injection in exported CSV.

### Routes

| Route            | Method | Description                              |
|------------------|--------|------------------------------------------|
| `/`              | GET    | Landing page with form                   |
| `/submit`        | POST   | Validates and stores submission          |
| `/thank-you`     | GET    | Confirmation page                        |
| `/admin/export`  | GET    | Downloads `submissions.csv`              |

The `/admin/export` route has **no authentication**. For a real deployment,
add HTTP Basic Auth or a secret token before exposing this.

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS submissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT UNIQUE NOT NULL,
    poll_answer TEXT NOT NULL,
    created_at  TEXT NOT NULL          -- ISO 8601, UTC timezone
);
```

- `email` has a `UNIQUE` constraint; duplicate submissions return a friendly
  error (caught via `sqlite3.IntegrityError`).
- Timestamps use `datetime.now(timezone.utc).isoformat()`.
- The database file (`database.db`) is **not committed to git** (`.gitignore`).

---

## Development Setup

```bash
cd idea_validator
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The app starts at `http://127.0.0.1:5000` with `debug=True`.

The SQLite database is created automatically on first run — no migration step
needed.

---

## Coding Conventions

### Python
- Standard library imports first, then third-party (`flask`), then local
  (`config`), separated by blank lines.
- Type annotations on all function signatures (Python 3.9+ style with
  `from __future__ import annotations`).
- Parameterised SQL queries only — never f-strings or `%` formatting in SQL.
- One DB connection per request; open with a `with` block so it auto-closes.
- Log meaningful events with `logger.info(...)` (already configured with
  `logging.basicConfig(level=logging.INFO)`).

### HTML / Jinja2
- Templates only receive values via `page_context()`; add new variables there.
- Jinja2 auto-escaping is active — do not use `| safe` unless you are certain
  the value is trusted HTML.
- Form input values are preserved on validation errors via `selected_poll_answer`
  and `email` context variables.

### CSS
- All colours and spacing use CSS custom properties defined at `:root` in
  `style.css`; modify those variables rather than hardcoding values.
- No JavaScript — keep interactions CSS-only (`:hover`, `:focus`).

---

## Security Checklist

When modifying the app, maintain these protections:

- **SQL injection** — always use `?` placeholders with `sqlite3`.
- **XSS** — rely on Jinja2 auto-escaping; never bypass with `| safe`.
- **CSV injection** — route all exported values through `csv_safe()`.
- **Input validation** — validate email format and poll answer against the
  known `config.POLL_OPTIONS` list server-side; never trust client data.
- **Admin export** — add authentication before deploying to a public URL.

---

## Adding Features

Follow these patterns when extending the project:

**New config value** → add to `config.py`, expose via `page_context()`.

**New form field** → add to the HTML form, read with `request.form.get()` in
`/submit`, validate, add a column to the `submissions` table (or a new table),
and include it in the CSV export.

**New route** → add a `@app.route(...)` function in `app.py`; use
`render_template(..., **page_context())` for pages that show site text.

**Avoid** adding JavaScript frameworks, ORMs, or new Python packages unless
the task genuinely requires them — the simplicity is intentional.

---

## Git Workflow

- Default branch: `master`
- Feature branches follow the pattern: `claude/<description>-<session-id>`
- The `database.db` file must never be committed (already in `.gitignore`).
- Commit messages should be concise and describe *what changed and why*.

### Branch for this session
```
claude/claude-md-mm6f63hxtn8f1lvf-OTJpT
```

---

## Deployment

See `README.md` for Render and Railway deployment instructions. The key points:

- Root directory must be set to `idea_validator/`.
- Start command: `python app.py`
- For production, replace `debug=True` with a proper WSGI server (e.g.,
  `gunicorn app:app`).
- SQLite is fine for low traffic; replace with PostgreSQL for concurrent writes.
