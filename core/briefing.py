from datetime import datetime, date

from core import memory
from core import relationship


def _time_of_day_greeting() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    if 12 <= hour < 17:
        return "Good afternoon"
    if 17 <= hour < 21:
        return "Good evening"
    return "Working late"


def _todays_reminders() -> list:
    """Return list of (text, time_str) for reminders due today."""
    today = date.today()
    out = []
    for r in memory.active_reminders():
        try:
            due = datetime.fromisoformat(r["due"])
        except (ValueError, KeyError):
            continue
        if due.date() == today:
            out.append((r["text"], due.strftime("%I:%M %p")))
    out.sort(key=lambda x: x[1])
    return out


def generate_briefing(preferred_name: str = "Sir") -> str:
    """
    Build the full morning briefing as a single spoken string.
    Sections are optional — missing data is silently skipped.
    """
    parts = []

    # 1. Greeting
    tod = _time_of_day_greeting()
    parts.append(f"{tod}, {preferred_name}.")

    # 2. Weather
    try:
        from commands.weather import get_current_weather_string
        weather = get_current_weather_string()
        if weather:
            parts.append(weather)
    except Exception as e:
        print(f"[briefing] weather failed: {e}")

    # 3. News
    try:
        from commands.news import get_headlines
        headlines = get_headlines(3)
        if headlines:
            if len(headlines) == 1:
                parts.append(f"Today's top headline: {headlines[0]}.")
            else:
                joined = ". ".join(headlines)
                parts.append(f"Today's top headlines: {joined}.")
    except Exception as e:
        print(f"[briefing] news failed: {e}")

    # 4. Today's reminders
    try:
        reminders = _todays_reminders()
        if reminders:
            if len(reminders) == 1:
                text, time_str = reminders[0]
                parts.append(f"One reminder today: {text} at {time_str}.")
            else:
                lines = "; ".join(f"{t} at {tm}" for t, tm in reminders)
                parts.append(f"{len(reminders)} reminders today: {lines}.")
    except Exception as e:
        print(f"[briefing] reminders failed: {e}")

    return " ".join(parts)