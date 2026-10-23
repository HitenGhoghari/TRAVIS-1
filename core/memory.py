import json
import os
import string
import uuid
from datetime import datetime
from config import BASE_DIR

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")


def _clean(text: str) -> str:
    """Remove surrounding whitespace and punctuation."""
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


# ---------- Facts memory ----------
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
    # Exact match first
    if key_clean in memory:
        return memory[key_clean]
    # Fuzzy: substring match either direction
    for k, v in memory.items():
        if key_clean in k or k in key_clean:
            return v
    return None


# ---------- Notes ----------
def load_notes():
    return _load(NOTES_FILE, [])


def save_notes(notes):
    _save(NOTES_FILE, notes)


def add_note(text: str):
    notes = load_notes()
    notes.append({
        "id": str(uuid.uuid4())[:8],
        "text": _clean(text),
        "created": datetime.now().isoformat(),
    })
    save_notes(notes)


def list_notes():
    return load_notes()


# ---------- Reminders ----------
def load_reminders():
    return _load(REMINDERS_FILE, [])


def save_reminders(reminders):
    _save(REMINDERS_FILE, reminders)


def add_reminder(text: str, due_iso: str):
    reminders = load_reminders()
    reminders.append({
        "id": str(uuid.uuid4())[:8],
        "text": _clean(text),
        "due": due_iso,
        "fired": False,
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


def mark_fired(reminder_id: str):
    reminders = load_reminders()
    for r in reminders:
        if r["id"] == reminder_id:
            r["fired"] = True
    save_reminders(reminders)