import datetime
import os


def _time(match, text):
    return datetime.datetime.now().strftime("It's %I:%M %p")


def _date(match, text):
    return datetime.datetime.now().strftime("Today is %A, %B %d, %Y")


def _day(match, text):
    return datetime.datetime.now().strftime("It's %A")


def _battery(match, text):
    try:
        import psutil
        b = psutil.sensors_battery()
        if b is None:
            return "I can't read the battery on this device."
        status = "charging" if b.power_plugged else "on battery"
        return f"Battery is at {round(b.percent)} percent, {status}."
    except ImportError:
        return "Please install psutil for battery info."


def _screenshot(match, text):
    try:
        import pyautogui
        from config import BASE_DIR
        path = os.path.join(BASE_DIR, "screenshot.png")
        pyautogui.screenshot(path)
        return "Screenshot saved to the project folder."
    except ImportError:
        return "Please install pyautogui for screenshots."


COMMANDS = [
    (r"\bwhat('s| is) the time\b|\btime now\b|\bcurrent time\b", _time),
    (r"\bwhat('s| is) (the|today's) date\b|\btoday's date\b", _date),
    (r"\bwhat day is it\b|\bwhat day is today\b", _day),
    (r"\bbattery\b|\bpower level\b", _battery),
    (r"\btake a screenshot\b|\bscreenshot\b|\bcapture screen\b", _screenshot),
]