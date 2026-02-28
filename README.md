# Idea Validation Landing Page

A minimal Flask app that collects an email address and a poll answer from visitors, stores everything in SQLite, and lets you download results as a CSV.

**Reuse it for any idea by editing a single file (`config.py`).**

---

## Quick Start (3 steps)

```bash
# 1. Enter the app folder and create a virtual environment
cd idea_validator
python -m venv .venv

# 2. Activate it and install Flask
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Open your browser at **http://127.0.0.1:5000** — the site is live.

---

## Customise for your own idea

**Edit only `idea_validator/config.py`.** Every line of user-facing text lives there:

```python
SITE_TITLE     = "My Idea"                # browser tab title
HEADLINE       = "Big bold hero text"     # main heading
DESCRIPTION    = "One or two sentences."  # subheading
POLL_QUESTION  = "What matters most?"     # question above the radio buttons
POLL_OPTIONS   = ["Option A", "Option B", "Option C"]  # 2–4 choices
SUBMIT_LABEL   = "Get Early Access"       # button text
THANK_YOU_TITLE   = "You're in!"
THANK_YOU_MESSAGE = "We'll be in touch."
```

Save the file and refresh the page — no restart needed in development.

---

## Project Structure

```
idea_validator/
├── app.py            ← Flask routes, DB logic, validation
├── config.py         ← ALL user-facing text lives here (edit this)
├── requirements.txt  ← single dependency: Flask
├── database.db       ← auto-created SQLite file (git-ignored)
├── templates/
│   ├── index.html    ← landing page / form
│   ├── thank_you.html
│   └── admin.html    ← admin dashboard
└── static/
    └── style.css
```

---

## Routes

| URL              | What it does                                   |
|------------------|------------------------------------------------|
| `/`              | Landing page with poll + email form            |
| `/submit`        | POST handler (validates & saves the form)      |
| `/thank-you`     | Confirmation page shown after a submission     |
| `/admin`         | Dashboard: submission count + download button  |
| `/admin/export`  | Downloads `submissions.csv` directly           |

---

## Reuse for a new idea

1. Copy the `idea_validator/` folder (give it a new name).
2. Edit `config.py` with your new idea's text.
3. Delete `database.db` so you start with a clean slate.
4. Run `python app.py`.

---

## Deploy for free

### Render (Web Service)

1. Push the repo to GitHub.
2. Create a new **Web Service** on [render.com](https://render.com).
3. Set **Root Directory** → `idea_validator`
4. **Build command** → `pip install -r requirements.txt`
5. **Start command** → `python app.py`

### Railway

1. Push the repo to GitHub.
2. Create a new project on [railway.app](https://railway.app), connect the repo.
3. Set **Root Directory** → `idea_validator`
4. **Start command** → `python app.py`

> **Note:** For production use a proper WSGI server:
> `gunicorn app:app`

---

## Notes

- The SQLite database (`database.db`) is created automatically on first run.
- `database.db` is git-ignored — it will never be committed.
- Duplicate emails are blocked at the database level.
- Email format is validated with a simple regex server-side.
- All user input is normalised and validated before being stored.
- New signups are printed to the console log.
- `/admin/export` has **no password**. Add authentication before making it public.
