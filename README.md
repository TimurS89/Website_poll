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

## Routes

- `/` → landing page
- `/submit` → POST form handler
- `/thank-you` → success page
- `/admin/export` → download CSV of submissions

## Reuse for another idea

Duplicate `idea_validator/` and edit only `config.py`:
- `SITE_TITLE`
- `HEADLINE`
- `DESCRIPTION`
- `POLL_QUESTION`
- `POLL_OPTIONS`

Everything in the HTML reads from these values dynamically.

## Simple deployment

### Render (Web Service)

- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
python app.py
```

Set root directory to `idea_validator`.

### Railway

- Deploy from repo
- Set root directory to `idea_validator`
- Start command:

```bash
python app.py
```

## Notes

- SQLite table `submissions` is auto-created if missing.
- `database.db` is intentionally not committed to git (SQLite is a binary file); it is created automatically on first run.
- Duplicate emails are blocked (`email` is unique).
- Basic email regex validation is included.
- Input is normalized and validated server-side.
- New signups are logged to console.

## Git branch note

All project files are committed in git in this repository history.
If you need this on `main`, merge or cherry-pick the latest work branch commit.
