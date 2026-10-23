import re
from commands import memory_skill, system, apps, media

# Add new skill modules to this list as you build them
SKILLS = [memory_skill, system, apps, media]


def handle(user_input: str):
    """
    Try to handle the command locally.
    Returns (handled: bool, reply: str | None).
    If no skill matches, returns (False, None) → caller falls through to Groq.
    """
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