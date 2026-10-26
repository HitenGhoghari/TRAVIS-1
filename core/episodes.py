import json
import os
import uuid
from datetime import datetime

from config import BASE_DIR

EPISODES_FILE = os.path.join(BASE_DIR, "data", "episodes.json")
MAX_EPISODES = 20


def load_episodes():
    if not os.path.exists(EPISODES_FILE):
        return []
    try:
        with open(EPISODES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_episodes(episodes):
    os.makedirs(os.path.dirname(EPISODES_FILE), exist_ok=True)
    with open(EPISODES_FILE, "w", encoding="utf-8") as f:
        json.dump(episodes[-MAX_EPISODES:], f, indent=2, ensure_ascii=False)


def add_episode(summary: str, message_count: int):
    if not summary or not summary.strip():
        return None
    episodes = load_episodes()
    episode = {
        "id": str(uuid.uuid4())[:8],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "summarized_at": datetime.now().isoformat(),
        "message_count": message_count,
        "summary": summary.strip(),
    }
    episodes.append(episode)
    save_episodes(episodes)
    return episode


def recent_for_prompt(n: int = 3) -> str:
    """Format the last N episodes for injection into the system prompt."""
    episodes = load_episodes()
    if not episodes:
        return ""
    recent = episodes[-n:]
    lines = []
    for ep in recent:
        date = ep.get("date", "unknown")
        summary = ep.get("summary", "").strip()
        if summary:
            lines.append(f"- {date}: {summary}")
    if not lines:
        return ""
    return "Recent session summaries:\n" + "\n".join(lines)