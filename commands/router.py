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
    conversation_skill,   # ← before memory_skill
    memory_skill,
    system,
    weather,
    news,
    timer_skill,
    clipboard_skill,
    apps,
    media,
]


def handle(user_input: str):
    text = user_input.lower().strip()

    for skill in SKILLS:
        for pattern, handler in skill.COMMANDS:
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