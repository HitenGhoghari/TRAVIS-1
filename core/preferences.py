import re
from core import relationship


# Decrease signals — "be brief from now on" or standalone "too long"
_DECREASE_STRONG = [
    r"\b(?:from now on|always|permanently|going forward)\b.*\b(?:brief|concise|short|shorter|terse|less detail)\b",
    r"\b(?:brief|concise|short|terse)\b.*\b(?:from now on|always|answers?)\b",
    r"\b(?:i prefer|i want|please make)\b.*\b(?:brief|concise|short|terse)\b",
]

_DECREASE_STANDALONE = [
    r"^\s*(?:that(?:'s| was| is))?\s*too\s+(?:long|verbose|wordy)\s*[.!?]?\s*$",
    r"^\s*(?:be\s+)?(?:more\s+)?(?:brief|concise)\s*[.!?]?\s*$",
    r"^\s*just (?:the )?facts\s*[.!?]?\s*$",
    r"^\s*(?:get|cut)\s+to\s+the\s+point\s*[.!?]?\s*$",
    r"^\s*(?:shorter|less detail|tldr|tl;?dr)\s*[.!?]?\s*$",
    r"^\s*stop\s+rambling\s*[.!?]?\s*$",
]

# Increase signals
_INCREASE_STRONG = [
    r"\b(?:from now on|always|permanently|going forward)\b.*\b(?:detail|detailed|longer|in.?depth|thorough|elaborate|more context)\b",
    r"\b(?:detailed|thorough|in.?depth|long)\b.*\b(?:from now on|always|answers?)\b",
    r"\b(?:i prefer|i want|please make)\b.*\b(?:detailed|thorough|long|in.?depth)\b",
]

_INCREASE_STANDALONE = [
    r"^\s*(?:be\s+)?(?:more\s+)?(?:detailed|thorough)\s*[.!?]?\s*$",
    r"^\s*more (?:detail|details|context)\s*[.!?]?\s*$",
    r"^\s*(?:longer|in.?depth)\s+answers?\s*[.!?]?\s*$",
    r"^\s*don'?t skip (?:the )?details?\s*[.!?]?\s*$",
    r"^\s*explain\s+(?:more|fully|thoroughly)\s*[.!?]?\s*$",
]

# Reset
_RESET = [
    r"^\s*(?:normal|default|medium)\s+(?:length|detail|verbosity)\s*[.!?]?\s*$",
    r"^\s*reset\s+(?:verbosity|preferences?|length)\s*[.!?]?\s*$",
    r"^\s*back\s+to\s+normal\s*[.!?]?\s*$",
]


def _matches(patterns, text):
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _current_verbosity():
    prefs = relationship.get_preferences()
    return int(prefs.get("verbosity", 3))


def _set_verbosity(value):
    value = max(1, min(10, int(value)))
    relationship.set_preference("verbosity", value)
    return value


def detect_preference_change(user_input: str):
    """
    Returns dict with 'reply' if a preference change was detected, else None.
    Called BEFORE skill routing — these are meta-commands.
    """
    if not user_input:
        return None

    text = user_input.strip()
    current = _current_verbosity()

    # Reset
    if _matches(_RESET, text):
        _set_verbosity(3)
        return {"reply": "Right, back to normal length.", "preference": "verbosity", "value": 3}

    # Decrease
    if _matches(_DECREASE_STRONG, text):
        new_val = _set_verbosity(2)
        return {
            "reply": "Understood. I'll keep answers brief from now on.",
            "preference": "verbosity",
            "value": new_val,
        }
    if _matches(_DECREASE_STANDALONE, text):
        if current <= 1:
            return {"reply": "I'm already as brief as I can be."}
        new_val = _set_verbosity(current - 1)
        return {
            "reply": "Noted — shorter answers from now on." if new_val <= 2 else "Noted, I'll trim the length.",
            "preference": "verbosity",
            "value": new_val,
        }

    # Increase
    if _matches(_INCREASE_STRONG, text):
        new_val = _set_verbosity(8)
        return {
            "reply": "Got it. I'll give more detail from now on.",
            "preference": "verbosity",
            "value": new_val,
        }
    if _matches(_INCREASE_STANDALONE, text):
        if current >= 10:
            return {"reply": "I'm already at maximum detail."}
        new_val = _set_verbosity(current + 1)
        return {
            "reply": "Understood — more detail from now on." if new_val >= 7 else "Noted, I'll add more detail.",
            "preference": "verbosity",
            "value": new_val,
        }

    return None