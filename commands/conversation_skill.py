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
    if count == 1:
        return "I remember our last exchange."
    return f"I remember our last {count} exchanges, going back to our first conversation on this device."


def _status_detail(match, text):
    if _brain is None:
        return "Conversation memory isn't available."
    count = _brain.exchange_count()
    if count == 0:
        return "My conversation memory is empty. I'm ready for a fresh start."
    return f"My conversation memory holds {count} exchanges. You can say 'clear conversation' to start fresh, or keep going — I'll remember what we discuss."


COMMANDS = [
    (r"\brepeat\s+(?:that|it)\b"
     r"|\bsay\s+(?:that|it)\s+again\b"
     r"|\bwhat\s+did\s+you\s+say\b"
     r"|\bcan\s+you\s+repeat\s+(?:that|it)?\b"
     r"|\bsay\s+that\s+one\s+more\s+time\b", _repeat),

    (r"\b(?:clear|forget|erase|wipe)\s+(?:the\s+|our\s+)?conversation\b"
     r"|\bforget\s+(?:our\s+)?(?:conversation|chat|history)\b"
     r"|\bclear\s+(?:your\s+|the\s+)?(?:conversation\s+)?(?:memory|history)\b",
     _clear_conversation),

    (r"\bhow\s+much\s+do\s+you\s+remember\b"
     r"|\bconversation\s+(?:status|history|memory)\b"
     r"|\bwhat\s+do\s+you\s+remember\s+(?:from|about)\s+our\s+(?:conversation|chat)\b",
     _conversation_status),

     # repeat
    (r"\brepeat\s+(?:that|it)\b|...", _repeat),

    # clear
    (r"\b(?:clear|forget|erase|wipe)\s+...", _clear_conversation),

    # count — short answer
    (r"\bhow\s+much\s+do\s+you\s+remember\b|...", _conversation_status),

    # status — longer, more informative
    (r"\bconversation\s+(?:status|history|memory)\b", _status_detail),
]