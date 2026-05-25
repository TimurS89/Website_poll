"""Configuration values for quickly reusing this landing page for new ideas.

Edit only this file when you duplicate the project for a different idea.
"""

SITE_TITLE = "Idea Validation"
HEADLINE = "Validate your next product idea before building"
DESCRIPTION = (
    "Join our early access list and tell us which direction matters most to you. "
    "We will share updates with people who sign up first."
)
POLL_QUESTION = "Which feature should we focus on first?"
POLL_OPTIONS = [
    "Simple MVP with core feature",
    "Automation and integrations",
    "Analytics dashboard",
    "Mobile-friendly experience",
]

# Optional community link shown on the thank-you page (Discord/Telegram/Slack/etc.).
# Leave blank to hide the button entirely.
COMMUNITY_URL = ""
COMMUNITY_LABEL = "Join the community"

# Message pre-filled when visitors share the page on social platforms.
SHARE_MESSAGE = "I just joined the early-access list — take a look:"

# Social proof. The participant counter shows max(PARTICIPANT_BASELINE, real signups):
# it reads "1,000+" until real sign-ups overtake the baseline, then switches to the
# true live number automatically. Set to 0 to display only the real count.
PARTICIPANT_BASELINE = 1000

# The poll result bars on the thank-you page appear only once this many REAL votes
# exist, so early percentages aren't dominated by one or two responses. The seeded
# counter above is never used to compute percentages — those are always real.
RESULTS_MIN_VOTES = 25
