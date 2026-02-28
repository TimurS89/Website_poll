"""Configuration values for quickly reusing this landing page for new ideas.

Edit ONLY this file when you duplicate the project for a different idea.
Every piece of user-facing text lives here — nothing is hardcoded in the HTML.
"""

# ── Page metadata ────────────────────────────────────────────────────────────
SITE_TITLE = "Idea Validation"

# ── SEO ───────────────────────────────────────────────────────────────────────
# Set SITE_URL to your production domain (no trailing slash) after deployment.
# Example: "https://myidea.onrender.com" or "https://www.mysite.com"
SITE_URL = ""
# Shown in Google search results snippets (150–160 characters recommended).
META_DESCRIPTION = (
    "Join our early access list and tell us which product direction matters most to you. "
    "Help shape what we build next."
)

# ── Landing page text ─────────────────────────────────────────────────────────
HEADLINE = "Validate your next product idea before building"
DESCRIPTION = (
    "Join our early access list and tell us which direction matters most to you. "
    "We will share updates with people who sign up first."
)

# ── Poll ──────────────────────────────────────────────────────────────────────
POLL_QUESTION = "Which feature should we focus on first?"
POLL_OPTIONS = [
    "Simple MVP with core feature",
    "Automation and integrations",
    "Analytics dashboard",
    "Mobile-friendly experience",
]

# ── Form button ───────────────────────────────────────────────────────────────
# Change this to match your call-to-action (e.g. "Join the waitlist", "Count me in").
SUBMIT_LABEL = "Get Early Access"

# ── Thank-you page ────────────────────────────────────────────────────────────
THANK_YOU_TITLE = "You're in!"
THANK_YOU_MESSAGE = "Your response has been recorded. We'll reach out with updates soon."
