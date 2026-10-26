import re

from core import memory

try:
    import pyperclip
    _HAS_PYPERCLIP = True
except ImportError:
    _HAS_PYPERCLIP = False

# Common Whisper mishearings of "clipboard"
_CLIPBOARD_WORD = r"(?:clipboard|click\s*board|clip\s*board)"

# Common forms of "note" (including "notepad" and Whisper's "not")
_NOTE_WORD = r"(?:notes?|notepad|not|memo)"


def _get_clipboard():
    if not _HAS_PYPERCLIP:
        return None
    try:
        text = pyperclip.paste()
    except Exception:
        return None
    if not text or not isinstance(text, str) or not text.strip():
        return None
    return text


def _read_clipboard(match, text):
    if not _HAS_PYPERCLIP:
        return "Clipboard support needs pyperclip installed. Run pip install pyperclip."
    content = _get_clipboard()
    if content is None:
        return "Your clipboard is empty, or it contains something I can't read, like an image."

    if len(content) > 400:
        preview = content[:400].rsplit(" ", 1)[0]
        return (f"Your clipboard contains: {preview}. "
                f"That's the first part; the full text is longer.")
    return f"Your clipboard contains: {content}"


def _copy(match, text):
    if not _HAS_PYPERCLIP:
        return "Clipboard support needs pyperclip installed. Run pip install pyperclip."

    # Group 1 may be from any of the alternative patterns
    content = None
    for i in range(1, len(match.groups()) + 1):
        if match.group(i):
            content = match.group(i)
            break

    if not content:
        return "What should I copy?"

    content = content.strip().strip(" .,!?:;\"'")
    if not content:
        return "What should I copy?"

    try:
        pyperclip.copy(content)
        preview = content if len(content) <= 60 else content[:60].rsplit(" ", 1)[0] + "…"
        return f"Copied to clipboard: {preview}."
    except Exception:
        return "Sorry, I couldn't copy that."


def _save_clipboard_as_note(match, text):
    if not _HAS_PYPERCLIP:
        return "Clipboard support needs pyperclip installed."
    content = _get_clipboard()
    if content is None:
        return "Your clipboard is empty or contains something I can't read."
    memory.add_note(content)
    preview = content if len(content) <= 60 else content[:60].rsplit(" ", 1)[0] + "…"
    return f"Saved to notes: {preview}."


def _clear_clipboard(match, text):
    if not _HAS_PYPERCLIP:
        return "Clipboard support needs pyperclip installed."
    try:
        pyperclip.copy("")
        return "Clipboard cleared."
    except Exception:
        return "Sorry, I couldn't clear the clipboard."


# Order matters — specific patterns must come BEFORE the generic "copy X"
COMMANDS = [
    # ---- Save clipboard as note ----
    (rf"\b(?:save|add|keep|store)\s+(?:my\s+|the\s+)?{_CLIPBOARD_WORD}"
     rf"\s+(?:as\s+(?:a\s+)?|to\s+(?:a\s+)?|in\s+(?:a\s+)?)?(?:my\s+)?{_NOTE_WORD}s?\b",
     _save_clipboard_as_note),
    (rf"\b(?:note|memo)\s+(?:down\s+)?(?:my\s+|the\s+)?{_CLIPBOARD_WORD}\b",
     _save_clipboard_as_note),

    # ---- Clear clipboard ----
    (rf"\bclear\s+(?:my\s+|the\s+)?{_CLIPBOARD_WORD}\b", _clear_clipboard),
    (rf"\bempty\s+(?:my\s+|the\s+)?{_CLIPBOARD_WORD}\b", _clear_clipboard),

    # ---- Read clipboard ----
    (rf"\b(?:what'?s|what is)\s+(?:in|on)\s+(?:my\s+|the\s+)?{_CLIPBOARD_WORD}\b",
     _read_clipboard),
    (rf"\b(?:read|show|tell\s+me|check)\s+(?:my\s+|the\s+)?{_CLIPBOARD_WORD}\b",
     _read_clipboard),
    (r"\bwhat\s+did\s+i\s+(?:just\s+)?copy\b", _read_clipboard),

    # ---- Copy text — MUST be last, it's a catch-all ----
    # Two alternatives because Whisper sometimes inserts punctuation after "copy"
    (r"\bcopy\s+(.+)", _copy),
    (r"\bcopy[.,:;!?]+\s*(.+)", _copy),
]