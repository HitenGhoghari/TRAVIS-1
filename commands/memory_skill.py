import re
from datetime import datetime, timedelta
from core import memory


WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
    "thirty": 30, "forty": 40, "sixty": 60,
}

_PUNCT = " .,?!:;"


def _strip_punct(text: str) -> str:
    return text.strip().strip(_PUNCT)


def _normalize_numbers(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\bin\s+a\s+(second|minute|min|hour|hr)", r"in 1 \1", text)
    for word, num in WORD_NUMBERS.items():
        text = re.sub(rf"\b{word}\b", str(num), text)
    return text


def _parse_time(text: str):
    text = _normalize_numbers(text)

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


# ---------- Remember ----------
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


# ---------- Recall: explicit ("what do you remember about...") ----------
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


# ---------- Recall: informal ("what's my...") — falls through if unknown ----------
def _recall_informal(match, text):
    key = _strip_punct(match.group(1))
    if not key:
        return None
    value = memory.recall(key)
    if value is None or value is True:
        return None
    
    # Find the FULL stored key that matched
    memory_dict = memory.load_memory()
    key_lower = key.lower()
    full_key = key
    for stored_key in memory_dict:
        if key_lower in stored_key or stored_key in key_lower:
            full_key = stored_key
            break
    
    # Strip leading "my " from the stored key, since we'll add "Your"
    display_key = re.sub(r"^my\s+", "", full_key, flags=re.IGNORECASE)
    return f"Your {display_key} is {value}."


# ---------- Remind ----------
def _remind(match, text):
    full = match.group(1).strip()
    normalized = _normalize_numbers(full)
    due = _parse_time(normalized)
    if due is None:
        return "I couldn't understand the time. Try 'remind me to call mom in 10 minutes'."

    reminder_text = re.sub(
        r"\b(in\s+\d+\s*(?:second|min|minute|hour|hr)s?"
        r"|tomorrow(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?"
        r"|at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        "", normalized, flags=re.IGNORECASE,
    )
    reminder_text = re.sub(r"\s+", " ", reminder_text)
    reminder_text = re.sub(
        r"\s+(remind|please|thanks?|okay?)\s*$", "", reminder_text,
        flags=re.IGNORECASE,
    )
    reminder_text = _strip_punct(reminder_text)

    if not reminder_text:
        reminder_text = "your reminder"

    memory.add_reminder(reminder_text, due)
    return f"Reminder set: {reminder_text}. I'll alert you at {due[11:16]}."


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


COMMANDS = [
    (r"\bremember that\s+(.+)", _remember),
    (r"\bwhat do you remember about\s+(.+)", _recall_explicit),
    (r"\bwhat'?s my\s+(.+)", _recall_informal),
    (r"\bwhat is my\s+(.+)", _recall_informal),
    (r"\btell me my\s+(.+)", _recall_informal),
    (r"\bdo you know my\s+(.+)", _recall_informal),
    (r"\bremind me to\s+(.+)", _remind),
    (r"\b(?:note that|add a note)\s+(.+)", _add_note),
    (r"\b(my notes|list notes|what are my notes)\b", _list_notes),
]