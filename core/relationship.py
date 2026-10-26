import json
import os
from datetime import datetime, date

from config import BASE_DIR

RELATIONSHIP_FILE = os.path.join(BASE_DIR, "data", "relationship.json")

_DEFAULT = {
    "first_interaction": None,
    "last_interaction": None,
    "last_session_date": None,
    "message_count": 0,
    "session_count": 0,
    "trust_level": 1,
    "preferred_name": "Sir",
    "learned_preferences": {
        "verbosity": 3,
        "humor": 5,
        "warmth": 4,
    },
    "shared_references": [],
    "mood_history": [],
}


def _load_raw():
    if not os.path.exists(RELATIONSHIP_FILE):
        return {k: (v.copy() if isinstance(v, (dict, list)) else v)
                for k, v in _DEFAULT.items()}
    try:
        with open(RELATIONSHIP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {k: (v.copy() if isinstance(v, (dict, list)) else v)
                for k, v in _DEFAULT.items()}


def load_relationship():
    data = _load_raw()
    for k, v in _DEFAULT.items():
        if k not in data:
            data[k] = (v.copy() if isinstance(v, (dict, list)) else v)
    return data


def save_relationship(data):
    os.makedirs(os.path.dirname(RELATIONSHIP_FILE), exist_ok=True)
    with open(RELATIONSHIP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _calculate_trust_level(data):
    """Trust grows with sessions, messages, and days. Caps at 10."""
    sessions = int(data.get("session_count", 0) or 0)
    messages = int(data.get("message_count", 0) or 0)
    first = data.get("first_interaction")
    days = 0
    if first:
        try:
            days = (date.today() - datetime.fromisoformat(first).date()).days
        except (ValueError, TypeError):
            days = 0
    raw = 1 + sessions // 5 + messages // 100 + days // 10
    return max(1, min(10, raw))


def start_session():
    """
    Call once at startup. Bumps session count, updates timestamps,
    recomputes trust. Returns True if this is the first session of the day.
    """
    data = load_relationship()
    now = datetime.now()
    today = date.today().isoformat()

    is_first_today = data.get("last_session_date") != today

    if not data.get("first_interaction"):
        data["first_interaction"] = now.isoformat()

    data["last_interaction"] = now.isoformat()
    data["last_session_date"] = today
    data["session_count"] = int(data.get("session_count", 0)) + 1
    data["trust_level"] = _calculate_trust_level(data)
    save_relationship(data)
    return is_first_today


def record_message():
    """Call once per user utterance (before routing to skills)."""
    data = load_relationship()
    data["message_count"] = int(data.get("message_count", 0)) + 1
    data["last_interaction"] = datetime.now().isoformat()
    data["trust_level"] = _calculate_trust_level(data)
    save_relationship(data)


def add_shared_reference(text):
    """Add a topic to shared references (deduped, max 20). For future use."""
    data = load_relationship()
    refs = data.get("shared_references", [])
    text = text.strip().lower()[:50]
    if text and text not in refs:
        refs.append(text)
        data["shared_references"] = refs[-20:]
        save_relationship(data)


def set_preference(key, value):
    """Update a learned preference. Used by Step 3."""
    data = load_relationship()
    prefs = data.get("learned_preferences", {})
    prefs[key] = max(1, min(10, int(value)))
    data["learned_preferences"] = prefs
    save_relationship(data)


def get_preferences():
    return load_relationship().get("learned_preferences", {})


def get_trust_level():
    return load_relationship().get("trust_level", 1)


def get_days_known():
    data = load_relationship()
    first = data.get("first_interaction")
    if not first:
        return 0
    try:
        return (date.today() - datetime.fromisoformat(first).date()).days
    except (ValueError, TypeError):
        return 0


def summary_line():
    data = load_relationship()
    return (
        f"trust={data.get('trust_level', 1)}/10 "
        f"sessions={data.get('session_count', 0)} "
        f"messages={data.get('message_count', 0)} "
        f"days={get_days_known()}"
    )