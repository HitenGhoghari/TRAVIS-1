import pyautogui


_muted = False


def _volume_up(match, text):
    for _ in range(5):
        pyautogui.press("volumeup")
    return "Turning the volume up."


def _volume_down(match, text):
    for _ in range(5):
        pyautogui.press("volumedown")
    return "Turning the volume down."


def _mute(match, text):
    global _muted
    if _muted:
        return "Already muted."
    pyautogui.press("volumemute")
    _muted = True
    return "Muted."


def _unmute(match, text):
    global _muted
    if not _muted:
        return "Not muted."
    pyautogui.press("volumemute")
    _muted = False
    return "Unmuted."


def _next_track(match, text):
    pyautogui.press("nexttrack")
    return "Skipping to next track."


def _prev_track(match, text):
    pyautogui.press("prevtrack")
    return "Going back to previous track."


def _play_pause(match, text):
    pyautogui.press("playpause")
    return "Toggled playback."


def _play(match, text):
    query = match.group(1).strip()
    if not query:
        return "What should I play?"
    try:
        import pywhatkit
        pywhatkit.playonyt(query)
        return f"Playing {query} on YouTube."
    except ImportError:
        return "Please install pywhatkit for YouTube playback."


COMMANDS = [
    (r"\b(volume up|turn it up|louder)\b", _volume_up),
    (r"\b(volume down|turn it down|quieter)\b", _volume_down),
    (r"\b(unmute|un-mute|turn (?:the )?sound on|turn (?:the )?audio on"
     r"|turn (?:my )?volume on|volume back on)\b", _unmute),
    (r"\b(mute|silence)\b", _mute),
    (r"\b(next (?:track|song))\b", _next_track),
    (r"\b(previous (?:track|song)|go back a (?:track|song)|last (?:track|song))\b", _prev_track),
    (r"\b(pause|play|resume|pause (?:the )?music|resume (?:the )?music)\b", _play_pause),
    (r"\bplay\s+(.+)", _play),
]