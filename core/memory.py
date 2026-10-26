import json
import os
import string
import uuid
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from config import BASE_DIR

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")


def _clean(text: str) -> str:
    return text.strip().strip(string.punctuation + " ")


def _load(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ---------- Facts ----------
def load_memory():
    return _load(MEMORY_FILE, {})


def save_memory(memory):
    _save(MEMORY_FILE, memory)


def remember(key: str, value: str):
    memory = load_memory()
    memory[_clean(key).lower()] = _clean(str(value))
    save_memory(memory)


def recall(key: str):
    key_clean = _clean(key).lower()
    memory = load_memory()
    if key_clean in memory:
        return memory[key_clean]
    for k, v in memory.items():
        if key_clean in k or k in key_clean:
            return v
    return None


# ---------- Notes ----------
def load_notes():
    return _load(NOTES_FILE, [])


def add_note(text: str):
    notes = load_notes()
    notes.append({
        "id": str(uuid.uuid4())[:8],
        "text": _clean(text),
        "created": datetime.now().isoformat(),
    })
    _save(NOTES_FILE, notes)


def list_notes():
    return load_notes()


# ---------- Reminders ----------
def load_reminders():
    return _load(REMINDERS_FILE, [])


def save_reminders(reminders):
    _save(REMINDERS_FILE, reminders)


def add_reminder(text: str, due_iso: str, recurrence: str = None,
                 interval_minutes: int = None):
    """
    recurrence: None, "daily", "weekly", "weekdays", "monthly", "interval"
    interval_minutes: used only when recurrence == "interval"
    """
    reminders = load_reminders()
    reminders.append({
        "id": str(uuid.uuid4())[:8],
        "text": _clean(text),
        "due": due_iso,
        "fired": False,
        "recurrence": recurrence,
        "interval_minutes": interval_minutes,
        "created": datetime.now().isoformat(),
    })
    save_reminders(reminders)
    return reminders[-1]["id"]


def get_due_reminders():
    now = datetime.now()
    due = []
    for r in load_reminders():
        if r.get("fired"):
            continue
        try:
            due_time = datetime.fromisoformat(r["due"])
        except (ValueError, KeyError):
            continue
        if due_time <= now:
            due.append(r)
    return due


def get_missed_reminders(grace_minutes: int = 5):
    """Reminders that were due more than `grace_minutes` ago — likely missed while offline."""
    now = datetime.now()
    missed = []
    for r in load_reminders():
        if r.get("fired"):
            continue
        try:
            due = datetime.fromisoformat(r["due"])
        except (ValueError, KeyError):
            continue
        if due < now - timedelta(minutes=grace_minutes):
            missed.append(r)
    return missed


def advance_reminder(reminder_id: str):
    """
    One-time → mark fired.
    Recurring → advance to the next future occurrence (skips missed slots,
    so it fires at most once per boot, not N times for N missed days).
    """
    reminders = load_reminders()
    now = datetime.now()

    for r in reminders:
        if r["id"] != reminder_id:
            continue

        rec = r.get("recurrence")
        if not rec:
            r["fired"] = True
            break

        current = datetime.fromisoformat(r["due"])
        next_due = current

        if rec == "daily":
            while next_due <= now:
                next_due += timedelta(days=1)

        elif rec == "weekly":
            while next_due <= now:
                next_due += timedelta(weeks=1)

        elif rec == "weekdays":
            next_due += timedelta(days=1)
            while next_due <= now or next_due.weekday() >= 5:
                next_due += timedelta(days=1)

        elif rec == "monthly":
            while next_due <= now:
                next_due = next_due + relativedelta(months=1)

        elif rec == "interval":
            minutes = r.get("interval_minutes") or 60
            step = timedelta(minutes=minutes)
            while next_due <= now:
                next_due += step

        r["due"] = next_due.isoformat()
        break

    save_reminders(reminders)


def cancel_reminder(query: str):
    reminders = load_reminders()
    query_lower = _clean(query).lower()
    for i, r in enumerate(reminders):
        text_lower = r["text"].lower()
        if query_lower == r["id"] or query_lower in text_lower or text_lower in query_lower:
            removed = reminders.pop(i)
            save_reminders(reminders)
            return removed["text"]
    return None


def active_reminders():
    return [r for r in load_reminders() if not r.get("fired")]