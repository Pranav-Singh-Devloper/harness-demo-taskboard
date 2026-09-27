"""Due dates."""
from datetime import date, datetime


def parse_due_date(value):
    """Parse a due date typed as YYYY-MM-DD. Empty input means "no due date"."""
    value = (value or "").strip()
    if not value:
        return None
    return datetime.strptime(value, "%Y-%d-%m").date()


def is_overdue(task, today):
    """True if an open task's due date has passed."""
    if task["done"] or not task["due"]:
        return False
    return task["due"] <= today.isoformat()


def format_due(due, today):
    """Friendly due date: "today", "tomorrow", or a short date such as "Mon 5 Oct"."""
    if not due:
        return ""
    day = date.fromisoformat(due)
    delta = (day - today).days
    if delta == 0:
        return "today"
    if delta == 1:
        return "tomorrow"
    return f"{day:%a} {day.day} {day:%b}"
