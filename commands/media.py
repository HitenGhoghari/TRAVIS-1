import pyautogui


def _volume_up(match, text):
    for _ in range(5):
        pyautogui.press("volumeup")
    return "Turning the volume up."


def _volume_down(match, text):
    for _ in range(5):
        pyautogui.press("volumedown")
    return "Turning the volume down."


def _mute(match, text):
    pyautogui.press("volumemute")
    return "Muted."


def _play(match, text):
    # Extract search term after "play"
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
    (r"\b(mute|silence)\b", _mute),
    (r"\bplay\s+(.+)", _play),
]