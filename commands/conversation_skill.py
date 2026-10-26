_speaker = None
_brain = None


def set_dependencies(speaker, brain):
    global _speaker, _brain
    _speaker = speaker
    _brain = brain


def _repeat(match, text):
    if _speaker is None:
        return "Repeat isn't available."
    last = getattr(_speaker, "last_spoken", "")
    if not last:
        return "I haven't said anything yet."
    return last


def _clear_conversation(match, text):
    if _brain is None:
        return "Conversation memory isn't available."
    _brain.clear_history()
    return "Conversation memory cleared."


def _conversation_status(match, text):
    if _brain is None:
        return "Conversation memory isn't available."
    count = _brain.exchange_count()
    if count == 0:
        return "I don't have any conversation history yet."
    return f"I remember the last {count} exchanges from our conversation."


# STRICT patterns only — each requires a specific phrase, no optional catch-alls.
COMMANDS = [
    # ---- Repeat ----
    (r"\brepeat that\b", _repeat),
    (r"\brepeat it\b", _repeat),
    (r"\bsay that again\b", _repeat),
    (r"\bsay it again\b", _repeat),
    (r"\bwhat did you say\b", _repeat),
    (r"\bcan you repeat\b", _repeat),
    (r"\bsay that one more time\b", _repeat),

    # ---- Clear conversation ----
    (r"\bclear conversation\b", _clear_conversation),
    (r"\bclear our conversation\b", _clear_conversation),
    (r"\bforget conversation\b", _clear_conversation),
    (r"\bforget our conversation\b", _clear_conversation),
    (r"\bforget chat\b", _clear_conversation),
    (r"\bforget history\b", _clear_conversation),
    (r"\bwipe conversation\b", _clear_conversation),
    (r"\bwipe memory\b", _clear_conversation),
    (r"\bclear memory\b", _clear_conversation),
    (r"\bclear history\b", _clear_conversation),

    # ---- Conversation status ----
    (r"\bhow much do you remember\b", _conversation_status),
    (r"\bconversation status\b", _conversation_status),
    (r"\bconversation history\b", _conversation_status),
    (r"\bconversation memory\b", _conversation_status),
]