import re
from datetime import datetime, timedelta
from core import memory


WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
    "thirty": 30, "forty": 40, "sixty": 60,
}

WEEKDAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}

_PUNCT = " .,?!:;"


def _strip_punct(text: str) -> str:
    return text.strip().strip(_PUNCT)


def _normalize(text: str) -> str:
    text = text.lower()
    # "12 p.m." → "12 pm"
    text = re.sub(r"\b([ap])\.m\.", r"\1m", text, flags=re.IGNORECASE)
    # "12 p.m" → "12 pm"
    text = re.sub(r"\b([ap])\.m\b", r"\1m", text, flags=re.IGNORECASE)
    # spelled numbers
    for word, num in WORD_NUMBERS.items():
        text = re.sub(rf"\b{word}\b", str(num), text)
    # "in a minute" → "in 1 minute"
    text = re.sub(r"\bin\s+a\s+(second|minute|min|hour|hr)", r"in 1 \1", text)
    return text


def _parse_time(text: str):
    text = _normalize(text)

    m = re.search(r"in\s+(\d+)\s*(second|min|minute|hour|hr)", text)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("sec"):
            delta = timedelta(seconds=n)
        elif unit.startswith("min"):
            delta = timedelta(minutes=n)
        else:
            delta = timedelta(hours=n)
        return (datetime.now() + delta).isoformat()

    if "tomorrow" in text:
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()

    m = re.search(r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target < now:
            target += timedelta(days=1)
        return target.isoformat()

    return None


def _extract_time_hm(text: str):
    text = _normalize(text)
    m = re.search(r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    ampm = m.group(3)
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    return hour, minute


def _next_weekday_at(weekday_name, hour, minute):
    target_wd = WEEKDAY_MAP[weekday_name.lower()]
    now = datetime.now()
    days_ahead = (target_wd - now.weekday()) % 7
    if days_ahead == 0:
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            days_ahead = 7
    target = (now + timedelta(days=days_ahead)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    return target.isoformat()


def _next_weekday_any(hour, minute):
    now = datetime.now()
    for offset in range(8):
        candidate = now + timedelta(days=offset)
        if candidate.weekday() < 5:
            target = candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target > now:
                return target.isoformat()
    return None


def _parse_recurrence(text: str):
    """
    Returns (recurrence, weekday_or_None, interval_minutes_or_None).
    recurrence: None, "daily", "weekly", "weekdays", "monthly", "interval"
    """
    text = _normalize(text)

    # interval: "every 2 hours", "every 30 minutes"
    m = re.search(r"\bevery\s+(\d+)\s*(second|min|minute|hour|hr)s?\b", text)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("sec"):
            minutes = max(1, n // 60)
        elif unit.startswith("min"):
            minutes = n
        else:
            minutes = n * 60
        return "interval", None, minutes

    if re.search(r"\b(every\s+(day|morning|evening|night)|daily)\b", text):
        return "daily", None, None
    if re.search(r"\b(every\s+week|weekly)\b", text):
        return "weekly", None, None
    if re.search(r"\bevery\s+weekday\b", text):
        return "weekdays", None, None
    if re.search(r"\b(every\s+month|monthly)\b", text):
        return "monthly", None, None

    m = re.search(r"\bevery\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text)
    if m:
        return "weekly", m.group(1), None

    return None, None, None


# ---------- Remember / recall ----------
def _remember(match, text):
    fact = match.group(1).strip()
    if not fact:
        return "What should I remember?"
    if " is " in fact:
        key, value = fact.split(" is ", 1)
        key_clean = _strip_punct(key)
        value_clean = _strip_punct(value)
        memory.remember(key_clean, value_clean)
        return f"Got it. I'll remember that {key_clean} is {value_clean}."
    memory.remember(_strip_punct(fact), True)
    return "Got it. I'll remember that."


def _recall_explicit(match, text):
    key = _strip_punct(match.group(1))
    if not key:
        return "What should I recall?"
    value = memory.recall(key)
    if value is None:
        return "I don't remember that yet."
    if value is True:
        return "Yes, I remember that."
    return f"{key} is {value}."


def _recall_informal(match, text):
    key = _strip_punct(match.group(1))
    if not key:
        return None
    value = memory.recall(key)
    if value is None or value is True:
        # If it looks like a password/PIN/code lookup, say so explicitly
        sensitive = ["password", "pin", "code", "passcode"]
        if any(w in key.lower() for w in sensitive):
            return f"I don't have a {key} stored in memory."
        return None

    # Find the full stored key for a nicer answer
    memory_dict = memory.load_memory()
    key_lower = key.lower()
    full_key = key
    for stored_key in memory_dict:
        if key_lower in stored_key or stored_key in key_lower:
            full_key = stored_key
            break

    # Strip leading "my " since we'll add "Your"
    import re as _re
    display_key = _re.sub(r"^my\s+", "", full_key, flags=_re.IGNORECASE)
    return f"Your {display_key} is {value}."


# ---------- Remind ----------
def _remind(match, text):
    raw = match.group(1).strip()
    raw = re.sub(r"^to\s+", "", raw, flags=re.IGNORECASE)
    normalized = _normalize(raw)

    recurrence, weekday, interval_minutes = _parse_recurrence(normalized)
    time_hm = _extract_time_hm(normalized)

    # --- First due time ---
    if recurrence == "interval" and interval_minutes:
        due = (datetime.now() + timedelta(minutes=interval_minutes)).isoformat()
    elif recurrence == "weekly" and weekday:
        hour, minute = time_hm if time_hm else (9, 0)
        due = _next_weekday_at(weekday, hour, minute)
    elif recurrence == "weekdays":
        hour, minute = time_hm if time_hm else (9, 0)
        due = _next_weekday_any(hour, minute)
    elif recurrence == "monthly":
        hour, minute = time_hm if time_hm else (9, 0)
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target = target + relativedelta(months=1)  # imported below
        due = target.isoformat()
    elif recurrence == "daily":
        due = _parse_time(normalized) if time_hm else (datetime.now() + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        ).isoformat()
    else:
        due = _parse_time(normalized)

    if due is None:
        return ("I couldn't understand the time. Try 'remind me to call mom in 10 minutes' "
                "or 'remind me every day at 8 am to take medicine'.")

    # --- Strip triggers from task text ---
    clean = normalized
    clean = re.sub(
        r"\b(every\s+\d+\s*(?:second|min|minute|hour|hr)s?|"
        r"every\s+(?:day|morning|evening|night|week|weekday|month|"
        r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
        r"daily|weekly|monthly)\b",
        "", clean, flags=re.IGNORECASE,
    )
    clean = re.sub(
        r"\b(in\s+\d+\s*(?:second|min|minute|hour|hr)s?"
        r"|tomorrow(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?"
        r"|at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        "", clean, flags=re.IGNORECASE,
    )
    clean = re.sub(r"\s+", " ", clean).strip()
    clean = re.sub(r"^(to|for|about)\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+(remind|please|thanks?|okay?)\s*$", "", clean, flags=re.IGNORECASE)
    clean = _strip_punct(clean)

    if not clean:
        return "What should I remind you about?"

    memory.add_reminder(clean, due, recurrence=recurrence,
                        interval_minutes=interval_minutes)

    due_dt = datetime.fromisoformat(due)
    time_str = due_dt.strftime("%H:%M")

    if recurrence == "daily":
        return f"Reminder set: {clean}. Every day at {time_str}."
    elif recurrence == "weekly" and weekday:
        return f"Reminder set: {clean}. Every {weekday.capitalize()} at {time_str}."
    elif recurrence == "weekly":
        return f"Reminder set: {clean}. Every week at {time_str}."
    elif recurrence == "weekdays":
        return f"Reminder set: {clean}. Every weekday at {time_str}."
    elif recurrence == "monthly":
        return f"Reminder set: {clean}. Every month on day {due_dt.day} at {time_str}."
    elif recurrence == "interval":
        return f"Reminder set: {clean}. Every {interval_minutes} minutes."
    else:
        return f"Reminder set: {clean}. I'll alert you at {time_str}."


# ---------- Cancel / list ----------
def _cancel_reminder(match, text):
    query = _strip_punct(match.group(1))
    if not query:
        return "What should I cancel?"
    removed = memory.cancel_reminder(query)
    if removed:
        return f"Cancelled reminder: {removed}."
    return f"I couldn't find a reminder matching '{query}'."


def _list_reminders(match, text):
    active = memory.active_reminders()
    if not active:
        return "You have no active reminders."

    active.sort(key=lambda r: r["due"])
    parts = []
    for r in active[:3]:
        due_dt = datetime.fromisoformat(r["due"])
        rec = r.get("recurrence")
        time_str = due_dt.strftime("%H:%M")
        if rec == "daily":
            parts.append(f"{r['text']} every day at {time_str}")
        elif rec == "weekly":
            parts.append(f"{r['text']} every week at {time_str}")
        elif rec == "weekdays":
            parts.append(f"{r['text']} every weekday at {time_str}")
        elif rec == "monthly":
            parts.append(f"{r['text']} every month on day {due_dt.day} at {time_str}")
        elif rec == "interval":
            parts.append(f"{r['text']} every {r.get('interval_minutes')} minutes")
        else:
            parts.append(f"{r['text']} at {time_str}")

    count = len(active)
    prefix = f"You have {count} reminders. Latest three: " if count > 3 else (
        "Your reminders: " if count > 1 else "Your reminder: "
    )
    return prefix + ". ".join(parts) + "."


# ---------- Notes ----------
def _add_note(match, text):
    note = (match.group(1) or match.group(2) or "").strip()
    if not note:
        return "What should I note down?"
    memory.add_note(_strip_punct(note))
    return "Note saved."


def _list_notes(match, text):
    notes = memory.list_notes()
    if not notes:
        return "You have no notes yet."
    latest = notes[-3:]
    return "Your latest notes are: " + ". ".join(n["text"] for n in latest)


# Imported here so `_remind` can use it
from dateutil.relativedelta import relativedelta


COMMANDS = [
    (r"\bremember that\s+(.+)", _remember),
    (r"\bwhat do you remember about\s+(.+)", _recall_explicit),
    (r"\bwhat'?s my\s+(.+)", _recall_informal),
    (r"\bwhat is my\s+(.+)", _recall_informal),
    (r"\btell me my\s+(.+)", _recall_informal),
    (r"\bdo you know my\s+(.+)", _recall_informal),

    (r"\bremind me\s+(.+)", _remind),
    # "every Monday at 10 am to check mail" without "remind me"
    (r"\bevery\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+.+", _remind),

    (r"\bcancel (?:my )?reminder\s+(.+)", _cancel_reminder),
    (r"\bdelete (?:my )?reminder\s+(.+)", _cancel_reminder),
    (r"\b(?:my reminders|list reminders|what are my reminders|show reminders)\b", _list_reminders),
    (r"\b(?:note that|add a note)\s+(.+)", _add_note),
    (r"\b(my notes|list notes|what are my notes)\b", _list_notes),
]