import re


_SOCIAL_PATTERNS = [
    r"\b(hi|hello|hey|good morning|good evening|good night)\b",
    r"\b(how are you|how'?s it going|what'?s up|how do you feel)\b",
    r"\b(thank you|thanks|nice job|well done|good work)\b",
    r"\b(joke|funny|make me laugh|tell me something interesting)\b",
    r"\b(you'?re (great|awesome|cool|amazing)|i like you)\b",
    r"\b(goodbye|bye|see you|good night)\b",
]

_SAFETY_PATTERNS = [
    r"\b(shut\s*down|restart|reboot|log\s*off|format|delete all)\b",
    r"\b(erase|wipe|destroy|remove everything)\b",
    r"\b(empty (the )?recycle bin)\b",
]

_TASK_PATTERNS = [
    r"\b(open|close|launch|start|stop|play|pause|mute|unmute)\b",
    r"\b(set|create|cancel|delete|remind|timer|alarm)\b",
    r"\b(what('?s| is) the (time|date|weather|news|battery))\b",
    r"\b(remember|recall|note|copy|clipboard|screenshot)\b",
    r"\b(brightness|volume|system info|battery)\b",
]


def _matches(patterns, text):
    return any(re.search(p, text) for p in patterns)


def classify_posture(user_text: str) -> str:
    text = user_text.lower().strip()

    if _matches(_SAFETY_PATTERNS, text):
        return "safety"
    if _matches(_TASK_PATTERNS, text):
        return "task"
    if _matches(_SOCIAL_PATTERNS, text):
        return "social"
    if "?" in text or text.startswith(("what", "who", "where", "when", "why", "how")):
        return "task"
    return "social"


def posture_note(posture: str) -> str:
    if posture == "social":
        return (
            "Posture: SOCIAL. Be warm, brief, and lightly witty. "
            "Match the user's mood. Do not launch into a task unless asked."
        )
    if posture == "safety":
        return (
            "Posture: SAFETY. Be explicit and formal. State exactly what will "
            "happen and what the user can say to cancel. Do not be casual."
        )
    return (
        "Posture: TASK. Be concise and efficient. Answer the request directly. "
        "No small talk unless the user initiates it."
    )


def classify_emotion_local(text: str, posture: str = "task") -> str:
    """Fallback emotion classifier when Groq forgets to tag."""
    t = text.lower()

    if posture == "safety":
        return "neutral"

    if any(w in t for w in ["sorry", "unfortunately", "sadly",
                             "passed away", "condolences", "i'm afraid"]):
        return "sad"

    if any(w in t for w in ["congratulations", "well done", "great news",
                             "awesome", "brilliant", "fantastic"]):
        return "happy"

    if any(w in t for w in ["wow", "incredible", "amazing", "unbelievable"]):
        return "excited"

    if any(w in t for w in ["careful", "warning", "danger", "alert"]):
        return "surprised"

    if any(w in t for w in ["obviously", "as i said", "clearly", "of course"]):
        return "sarcastic"

    return "neutral"