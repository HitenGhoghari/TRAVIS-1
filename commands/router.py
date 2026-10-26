import re
from commands import (
    about,
    conversation_skill,
    memory_skill,
    system,
    weather,
    news,
    timer_skill,
    clipboard_skill,
    apps,
    media,
)

SKILLS = [
    about,
    conversation_skill,
    memory_skill,
    system,
    weather,
    news,
    timer_skill,
    clipboard_skill,
    apps,
    media,
]


def _is_safe_pattern(pattern: str) -> bool:
    """Reject empty or trivially-matching patterns."""
    if not pattern or not pattern.strip():
        return False
    # Reject patterns that match empty string (catch-alls)
    try:
        if re.search(pattern, "") is not None:
            return False
    except re.error:
        return False
    return True


def handle(user_input: str):
    text = user_input.lower().strip()

    for skill in SKILLS:
        for entry in getattr(skill, "COMMANDS", []):
            if not isinstance(entry, tuple) or len(entry) != 2:
                continue
            pattern, handler = entry

            if not _is_safe_pattern(pattern):
                print(f"[WARNING] Skipping unsafe pattern in {skill.__name__}: {pattern!r}")
                continue

            match = re.search(pattern, text)
            if match:
                try:
                    reply = handler(match, text)
                    if reply:
                        return True, reply
                except Exception as e:
                    print(f"[Skill error: {skill.__name__}] {e}")
                    return True, "Sorry, I couldn't execute that command."

    return False, None