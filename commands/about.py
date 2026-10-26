from commands import router


def _what_can_i_do(match, text):
    total_commands = sum(len(skill.COMMANDS) for skill in router.SKILLS)
    skill_count = len(router.SKILLS)

    descriptions = [
        "check the weather, rain, forecast, and air quality",
        "set timers, reminders, and recurring alerts",
        "remember facts, take notes, and recall information",
        "control volume, mute, and media playback",
        "check battery, system info, and take screenshots",
        "adjust brightness, lock, sleep, restart, or shut down your computer",
        "read, copy, save, and clear your clipboard",
        "open and close applications and websites",
        "get today's news headlines",
        "search the web for real-time information",
    ]

    return (
        f"I currently have {total_commands} commands across {skill_count} skill modules. "
        f"I can help you {', '.join(descriptions)}. "
        f"I can also answer any general knowledge question using my AI brain, "
        f"and I remember facts you tell me locally."
    )


COMMANDS = [
    (r"\bwhat can you do\b", _what_can_i_do),
    (r"\bwhat are your capabilities\b", _what_can_i_do),
    (r"\bwhat can you help with\b", _what_can_i_do),
    (r"\bwhat are you able to do\b", _what_can_i_do),
]