import re

EMOTIONS = {
    "neutral", "happy", "sad", "angry",
    "excited", "disgust", "sarcastic", "surprised",
}

ALIASES = {
    "joy": "happy",
    "anger": "angry",
    "surprise": "surprised",
    "disgusted": "disgust",
    "sarcasm": "sarcastic",
    "calm": "neutral",
    "serious": "neutral",
    "fear": "surprised",
    "afraid": "surprised",
    "amused": "happy",
    "annoyed": "angry",
}

TAG_RE = re.compile(r"\[([a-zA-Z]+)\]")


def normalize_emotion(name: str) -> str:
    if not name:
        return "neutral"
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    return key if key in EMOTIONS else "neutral"


def parse_spans(text: str):
    """
    Split tagged text into (emotion, span_text) pairs.
    Tags are removed from span_text.
    If no tags are present, returns [(neutral, text)].
    """
    spans = []
    current = "neutral"
    pos = 0

    for m in TAG_RE.finditer(text):
        segment = text[pos:m.start()]
        if segment.strip():
            spans.append((current, segment.strip()))
        current = normalize_emotion(m.group(1))
        pos = m.end()

    tail = text[pos:]
    if tail.strip():
        spans.append((current, tail.strip()))

    if not spans:
        spans = [("neutral", text.strip())]

    return spans


def strip_tags(text: str) -> str:
    return TAG_RE.sub("", text).strip()