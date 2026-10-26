import ctypes
import datetime
import os
import subprocess
import time

import psutil


# ---------- Info ----------
def _time(match, text):
    return datetime.datetime.now().strftime("It's %I:%M %p")


def _date(match, text):
    return datetime.datetime.now().strftime("Today is %A, %B %d, %Y")


def _day(match, text):
    return datetime.datetime.now().strftime("It's %A")


def _battery(match, text):
    try:
        b = psutil.sensors_battery()
        if b is None:
            return "I can't read the battery on this device."
        status = "charging" if b.power_plugged else "on battery"
        return f"Battery is at {round(b.percent)} percent, {status}."
    except Exception:
        return "I can't read the battery on this device."


def _system_info(match, text):
    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory()
    try:
        disk = psutil.disk_usage("C:\\")
        disk_pct = round(disk.percent)
    except Exception:
        disk_pct = "unknown"
    uptime = time.time() - psutil.boot_time()
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    return (f"CPU at {round(cpu)} percent. "
            f"RAM {round(ram.percent)} percent used. "
            f"Disk {disk_pct} percent used. "
            f"Uptime {hours} hours {minutes} minutes.")


def _screenshot(match, text):
    try:
        import pyautogui
        from config import BASE_DIR
        path = os.path.join(BASE_DIR, "screenshot.png")
        pyautogui.screenshot(path)
        return "Screenshot saved to the project folder."
    except Exception:
        return "Screenshot failed. Check that Pillow is installed."


# ---------- Brightness ----------
def _brightness_get():
    try:
        import screen_brightness_control as sbc
        levels = sbc.get_brightness()
        return levels[0] if levels else None
    except Exception:
        return None


def _brightness_up(match, text):
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness("+20")
        level = _brightness_get()
        return f"Brightness at {level} percent." if level else "Brightness increased."
    except ImportError:
        return "Brightness control needs screen-brightness-control installed."
    except Exception:
        return "I can't control brightness on this display."


def _brightness_down(match, text):
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness("-20")
        level = _brightness_get()
        return f"Brightness at {level} percent." if level else "Brightness decreased."
    except ImportError:
        return "Brightness control needs screen-brightness-control installed."
    except Exception:
        return "I can't control brightness on this display."


def _brightness_set(match, text):
    try:
        level = int(match.group(1))
        if not 0 <= level <= 100:
            return "Brightness must be between 0 and 100."
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
        return f"Brightness set to {level} percent."
    except ImportError:
        return "Brightness control needs screen-brightness-control installed."
    except Exception:
        return "I can't control brightness on this display."


# ---------- Power ----------
def _lock(match, text):
    ctypes.windll.user32.LockWorkStation()
    return "Locking."


def _sleep(match, text):
    # Hibernate=FALSE, ForceCritical=TRUE, DisableWakeEvent=FALSE
    ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
    return "Going to sleep."


def _restart(match, text):
    subprocess.run(
        'shutdown /r /t 120 /c "TRAVIS: Restart in 120 seconds. '
        'Say: cancel restart. Or: stop. Or: cancel."',
        shell=True,
    )
    return (
        "Restarting in 120 seconds. "
        "Say cancel restart, or just say stop, or say cancel, to abort."
    )


def _shutdown(match, text):
    subprocess.run(
        'shutdown /s /t 120 /c "TRAVIS: Shutdown in 120 seconds. '
        'Say: cancel shutdown. Or: stop. Or: cancel."',
        shell=True,
    )
    return (
        "Shutting down in 120 seconds. "
        "Say cancel shutdown, or just say stop, or say cancel, to abort."
    )


def _logoff(match, text):
    subprocess.run('shutdown /l', shell=True)
    return "Logging off."


def _cancel_shutdown(match, text):
    result = subprocess.run(
        "shutdown /a", shell=True, capture_output=True, text=True
    )
    if result.returncode == 0:
        return "Cancelled. No restart or shutdown will happen."
    return "There's nothing to cancel."


# ---------- Recycle bin ----------
def _empty_recycle(match, text):
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
            shell=True,
            timeout=15
        )
        return "Recycle bin emptied."
    except Exception:
        return "I couldn't empty the recycle bin."


# ---------- Command table ----------
# ORDER MATTERS — cancel, then destructive, then informational
COMMANDS = [
    # Cancel MUST come before shutdown/restart
        # ---- Cancel patterns — put these FIRST, before any restart/shutdown ----

    # "cancel" anywhere + restart/shutdown/reboot anywhere (order agnostic)
    (r"\bcancel\b.*\b(?:shutdown|restart|reboot|shut\s*down|power\s*off|log\s*off)\b",
     _cancel_shutdown),
    (r"\b(?:shutdown|restart|reboot|shut\s*down|power\s*off|log\s*off)\b.*\bcancel\b",
     _cancel_shutdown),

    # "stop / abort / halt / prevent" + action word
    (r"\b(?:stop|abort|halt|prevent|kill|end)\b.*\b(?:shutdown|restart|reboot|shut\s*down)\b",
     _cancel_shutdown),
    (r"\b(?:shutdown|restart|reboot|shut\s*down)\b.*\b(?:stop|abort|halt|prevent|cancel|kill)\b",
     _cancel_shutdown),

    # "don't restart / no restart / not restart"
    (r"\b(?:don'?t|do\s+not|no|not)\s+(?:restart|shut\s*down|reboot|log\s*off)\b",
     _cancel_shutdown),

    # Standalone phrases — "cancel", "abort", "never mind", "forget it"
    (r"^\s*(?:cancel|abort|halt)\s*[.!?]?\s*$", _cancel_shutdown),
    (r"^\s*never\s*mind\s*[.!?]?\s*$", _cancel_shutdown),
    (r"^\s*forget\s+(?:it|that|about\s+it)\s*[.!?]?\s*$", _cancel_shutdown),
    (r"^\s*(?:stop|wait)\s*[.!?]?\s*$", _cancel_shutdown),
    (r"^\s*stop\s+(?:it|that)\s*[.!?]?\s*$", _cancel_shutdown),
    (r"^\s*don'?t\s+(?:do\s+it|do\s+that)\s*[.!?]?\s*$", _cancel_shutdown),

    # Legacy explicit form
    (r"\bcancel\s+(?:the\s+)?(?:shutdown|restart|reboot)\b", _cancel_shutdown),
    (r"\babort\s+(?:the\s+)?(?:shutdown|restart|reboot)\b", _cancel_shutdown),

    # Power controls — target noun required to avoid false matches
    (r"\block\s+(?:the\s+)?(?:screen|computer|pc|system|laptop)\b"
     r"|\block\s+(?:it|now)\b", _lock),
    (r"\bsleep\s+mode\b"
    r"|\bput\s+(?:the\s+)?(?:computer|pc|system|laptop)\s+to\s+sleep\b"
    r"|\bturn\s+(?:my\s+|the\s+)?(?:computer|pc|system|laptop)\s+(?:in)?to\s+sleep\b"
    r"|\bsleep\s+(?:my\s+|the\s+)?(?:computer|pc|system|laptop)\b"
    r"|\bsuspend\s+(?:the\s+)?(?:computer|pc|system|laptop)\b", _sleep),
    (r"\brestart\s+(?:the\s+)?(?:computer|pc|system|laptop)\b"
     r"|\breboot\s+(?:the\s+)?(?:computer|pc|system|laptop)?\b", _restart),
    (r"\bshut\s*down\s+(?:the\s+)?(?:computer|pc|system|laptop)\b"
     r"|\bpower\s+off\s+(?:the\s+)?(?:computer|pc|laptop)\b"
     r"|\bturn\s+off\s+(?:the\s+)?(?:computer|pc|laptop)\b", _shutdown),
    (r"\blog\s*(?:off|out)\b", _logoff),

    # Brightness
    (r"\bbrightness\s+up\b"
     r"|\bincrease\s+(?:the\s+)?brightness\b"
     r"|\bbrighter\b", _brightness_up),
    (r"\bbrightness\s+down\b"
     r"|\bdecrease\s+(?:the\s+)?brightness\b"
     r"|\bdimmer\b|\bdim\s+(?:the\s+)?(?:screen|display)\b", _brightness_down),
    (r"\b(?:set\s+)?brightness\s+(?:to\s+)?(\d{1,3})\b", _brightness_set),

    # System info
    (r"\bsystem\s+(?:info|status|health)\b"
     r"|\bhow'?s\s+(?:my|the)\s+(?:system|computer)\b"
     r"|\bhow\s+is\s+(?:my|the)\s+(?:system|computer)\b", _system_info),

    # Recycle bin
    (r"\b(?:empty|clear)\s+(?:the\s+)?recycle\s*bin\b", _empty_recycle),

    # Info
    (r"\bwhat\s+time\s+is\s+it\b"
     r"|\btime\s+is\s+it\b"
     r"|\bwhat('s| is) the time\b"
     r"|\bwhat'?s\s+time\b"
     r"|\btime now\b"
     r"|\bcurrent time\b"
     r"|\btell me (?:the )?time\b", _time),
    (r"\bwhat('s| is) (?:the |today'?s )?date\b"
     r"|\bdate\s+is\s+it\b"
     r"|\btoday'?s date\b"
     r"|\bwhat date is it\b", _date),
    (r"\bwhat day (?:of the week )?is it\b"
     r"|\bday\s+is\s+it\b"
     r"|\bwhat day is today\b", _day),
    (r"\bbattery\b|\bpower level\b", _battery),
    (r"\btake a screenshot\b|\bscreenshot\b|\bcapture screen\b", _screenshot),
]