import ctypes
import os
import subprocess
import time
import webbrowser

import psutil


# ---------- Graceful close (WM_CLOSE, no force-kill) ----------
def _close_by_name(process_name: str, display_name: str) -> str:
    EnumWindows = ctypes.windll.user32.EnumWindows
    GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
    PostMessageW = ctypes.windll.user32.PostMessageW
    WM_CLOSE = 0x0010
    my_pid = os.getpid()
    windows_found = [0]

    def callback(hwnd, _):
        pid = ctypes.c_ulong()
        GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == my_pid:
            return True
        try:
            proc = psutil.Process(pid.value)
            if proc.name().lower() == process_name.lower():
                windows_found[0] += 1
                PostMessageW(hwnd, WM_CLOSE, 0, 0)
        except Exception:
            pass
        return True

    EnumWindows(
        ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(callback),
        0,
    )

    if windows_found[0] > 0:
        return f"Asked {display_name} to close."
    return f"{display_name} doesn't seem to be open."


def _close_notepad(match, text):
    return _close_by_name("notepad.exe", "Notepad")


def _close_chrome(match, text):
    return _close_by_name("chrome.exe", "Chrome")


# ---------- Verified open ----------
def _open_verified(name_pattern: str, command: str, display_name: str) -> str:
    def get_pids():
        return {
            p.pid for p in psutil.process_iter(["name"])
            if name_pattern in (p.info["name"] or "").lower()
        }

    before = get_pids()
    try:
        subprocess.Popen(command, shell=True)
    except Exception as e:
        return f"I couldn't launch {display_name}: {e}"

    time.sleep(1.5)
    after = get_pids()

    if after - before:
        return f"{display_name} is running."
    if before:
        return f"{display_name} was already running."
    return f"I couldn't confirm {display_name} started."


def _open_chrome(match, text):
    return _open_verified("chrome", r"start chrome", "Chrome")


def _open_notepad(match, text):
    return _open_verified("notepad", "notepad.exe", "Notepad")


def _open_calc(match, text):
    return _open_verified("calc", "calc.exe", "Calculator")


def _open_explorer(match, text):
    return _open_verified("explorer", "explorer.exe", "File Explorer")


# ---------- Websites ----------
def _open_youtube(match, text):
    webbrowser.open("https://youtube.com")
    return "Opening YouTube."


def _open_google(match, text):
    webbrowser.open("https://google.com")
    return "Opening Google."


def _open_github(match, text):
    webbrowser.open("https://github.com")
    return "Opening GitHub."


COMMANDS = [
    (r"\bopen chrome\b|\blaunch chrome\b", _open_chrome),
    (r"\bopen notepad\b|\blaunch notepad\b", _open_notepad),
    (r"\bopen (calculator|calc)\b|\blaunch (calculator|calc)\b", _open_calc),
    (r"\bopen (file )?explorer\b", _open_explorer),
    (r"\bopen youtube\b", _open_youtube),
    (r"\bopen google\b", _open_google),
    (r"\bopen github\b", _open_github),

    (r"^\s*chrome\s*\.?$", _open_chrome),
    (r"^\s*notepad\s*\.?$", _open_notepad),
    (r"^\s*(calculator|calc)\s*\.?$", _open_calc),
    (r"^\s*explorer\s*\.?$", _open_explorer),

    (r"\bclose notepad\b", _close_notepad),
    (r"\bclose chrome\b", _close_chrome),
]