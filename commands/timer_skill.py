import re
import threading
import uuid

_speaker = None
_active = {}

_WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
    "thirty": 30, "forty": 40, "sixty": 60,
}

_PUNCT = " .,?!:;"


def set_speaker(speaker):
    global _speaker
    _speaker = speaker


def _strip_punct(text: str) -> str:
    return text.strip().strip(_PUNCT)


def _normalize_numbers(text: str) -> str:
    text = text.lower()
    for word, num in _WORD_NUMBERS.items():
        text = re.sub(rf"\b{word}\b", str(num), text)
    return text


def _parse_duration(text: str):
    text = _normalize_numbers(text)
    m = re.search(r"(\d+)\s*(second|sec|minute|min|hour|hr)", text)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    if unit.startswith("sec"):
        return n
    if unit.startswith("min"):
        return n * 60
    return n * 3600


def _fire(timer_id, label):
    if _speaker:
        _speaker.speak(f"Timer finished: {label}.")
    _active.pop(timer_id, None)


def _set_timer(match, text):
    duration = _parse_duration(text)
    if duration is None:
        return "I couldn't understand the duration. Try 'set a timer for 10 minutes'."

    label = re.sub(
        r"\b(?:set|start|create)?\s*(?:a\s+)?timer\s+(?:for\s+)?"
        r"\d+\s*(?:second|sec|minute|min|hour|hr)s?"
        r"(?:\s+(?:to|for|called)\s+(.+))?",
        lambda m: m.group(1) or "",
        _normalize_numbers(text),
        flags=re.IGNORECASE,
    ).strip()
    label = _strip_punct(label) or "timer"

    timer_id = str(uuid.uuid4())[:8]
    timer = threading.Timer(duration, _fire, args=(timer_id, label))
    timer.daemon = True
    _active[timer_id] = {"timer": timer, "label": label, "duration": duration}
    timer.start()

    minutes, seconds = divmod(duration, 60)
    if minutes and seconds:
        spoken = f"{minutes} minutes and {seconds} seconds"
    elif minutes:
        spoken = f"{minutes} minutes"
    else:
        spoken = f"{seconds} seconds"
    return f"Timer set for {spoken}."


def _cancel_timer(match, text):
    query = _strip_punct(match.group(1) or "").lower()
    if not query:
        return "What timer should I cancel?"
    for tid, info in list(_active.items()):
        if query in info["label"].lower() or query == tid:
            info["timer"].cancel()
            _active.pop(tid)
            return f"Cancelled timer: {info['label']}."
    return f"I couldn't find a timer matching '{query}'."


def _list_timers(match, text):
    if not _active:
        return "You have no active timers."
    parts = []
    for info in _active.values():
        minutes, seconds = divmod(info["duration"], 60)
        if minutes and seconds:
            length = f"{minutes} minutes {seconds} seconds"
        elif minutes:
            length = f"{minutes} minutes"
        else:
            length = f"{seconds} seconds"
        parts.append(f"{info['label']} for {length}")
    return "Active timers: " + ". ".join(parts) + "."


COMMANDS = [
    (r"\b(?:set|start|create)?\s*(?:a\s+)?timer\s+(?:for\s+)?\d+\s*(?:second|sec|minute|min|hour|hr)s?.+", _set_timer),
    (r"\b(?:set|start|create)?\s*(?:a\s+)?timer\s+(?:for\s+)?\d+\s*(?:second|sec|minute|min|hour|hr)s?", _set_timer),
    (r"\bcancel\s+(?:the\s+)?timer\s+(.+)", _cancel_timer),

    # Broader list patterns
    (r"\b(?:my|list|any|which)\s+timers?\b", _list_timers),
    (r"\bwhat'?s?\s+timers?\b", _list_timers),
    (r"\btimers?,?\s+do\s+i\s+have\b", _list_timers),
    (r"\bdo\s+i\s+have\s+(?:any\s+)?timers?\b", _list_timers),
    # Whisper often drops the "r" — accommodate "what time do I have"
    (r"\bwhat\s+time\s+do\s+i\s+have\b", _list_timers),
]