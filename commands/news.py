import json
import os
import random

import feedparser

from config import NEWS_MAX_SEEN, BASE_DIR

DATA_DIR = os.path.join(BASE_DIR, "data")
SEEN_FILE = os.path.join(DATA_DIR, "seen_news.json")

# Google News India — aggregator, free, no key
GOOGLE_NEWS_TOP = (
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
)
GOOGLE_NEWS_SEARCH = (
    "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
)

# Fallback RSS feeds if Google News is unreachable
FALLBACK_TOP_FEEDS = [
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
]


def _load_seen():
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_seen(seen):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen[-NEWS_MAX_SEEN:], f, indent=2)


def _parse_feed(url):
    try:
        feed = feedparser.parse(
            url,
            request_headers={"User-Agent": "Mozilla/5.0 (TRAVIS)"},
        )
    except Exception as e:
        print(f"[news feed error] {url}: {e}")
        return []

    articles = []
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        if not title:
            continue

        source = ""
        # Google News titles often end with " - Source Name"
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            if len(parts) == 2:
                t, s = parts[0].strip(), parts[1].strip()
                if t and s and len(s) < 60:
                    title = t
                    source = s

        articles.append({
            "title": title,
            "source": source,
            "url": entry.get("link") or title,
        })
    return articles


def _clean_topic(topic):
    if not topic:
        return None
    topic = topic.strip().strip(" .,!?;:")
    return topic or None


def _get_news(match, text):
    raw_topic = match.group(1) if match.groups() else None
    topic = _clean_topic(raw_topic)

    if topic:
        query = topic.replace(" ", "+")
        url = GOOGLE_NEWS_SEARCH.format(query=query)
        articles = _parse_feed(url)
        intro = f"Here are the top headlines about {topic}: "
    else:
        articles = _parse_feed(GOOGLE_NEWS_TOP)
        # Fallback to Times of India / NDTV if Google is thin
        if len(articles) < 3:
            for fallback in FALLBACK_TOP_FEEDS:
                more = _parse_feed(fallback)
                if more:
                    articles.extend(more)
                    if len(articles) >= 10:
                        break
        intro = "Here are today's top headlines from India: "

    if not articles:
        print("[news] all feeds returned empty")
        return "I couldn't reach any news source right now."

    # Dedup within this call
    seen_urls = set()
    valid = []
    for a in articles:
        if a["url"] in seen_urls:
            continue
        seen_urls.add(a["url"])
        valid.append(a)

    # Filter out already-seen
    seen = _load_seen()
    seen_set = set(seen)
    unseen = [a for a in valid if a["url"] not in seen_set]

    if not unseen:
        # Everything seen — reset and reuse
        seen = []
        seen_set = set()
        unseen = valid

    random.shuffle(unseen)
    picked = unseen[:3]

    for a in picked:
        if a["url"] and a["url"] not in seen_set:
            seen.append(a["url"])
            seen_set.add(a["url"])
    _save_seen(seen)

    headlines = []
    for a in picked:
        if a["source"]:
            headlines.append(f"From {a['source']}: {a['title']}")
        else:
            headlines.append(a["title"])

    return intro + ". ".join(headlines) + "."


COMMANDS = [
    (r"\bwhat'?s\s+(?:the\s+)?news\b"
     r"|\bwhat\s+is\s+(?:today'?s\s+)?news\b"
     r"|\b(?:give\s+me|tell\s+me|show\s+me)\s+(?:today'?s\s+|the\s+)?news\b"
     r"|\bnews\s+headlines?\b", _get_news),

    (r"\bnews\s+(?:about|on|for)\s+(.+)", _get_news),
    (r"\b(?:tell\s+me|give\s+me|show\s+me)\s+(?:the\s+)?news\s+(?:about|on|for)\s+(.+)", _get_news),
]


def get_headlines(n=3, topic=None) -> list:
    """
    Public API for briefing module.
    Returns a list of headline strings, or [] on failure.
    """
    try:
        if topic:
            query = topic.replace(" ", "+")
            url = GOOGLE_NEWS_SEARCH.format(query=query)
        else:
            url = GOOGLE_NEWS_TOP

        articles = _parse_feed(url)
        if not articles:
            return []

        # Dedup + skip already-seen
        seen = _load_seen()
        seen_set = set(seen)
        unseen = [a for a in articles if a["url"] not in seen_set]

        if not unseen:
            unseen = articles

        random.shuffle(unseen)
        picked = unseen[:n]

        # Mark picked as seen
        for a in picked:
            if a["url"] and a["url"] not in seen_set:
                seen.append(a["url"])
                seen_set.add(a["url"])
        _save_seen(seen)

        return [a["title"] for a in picked if a.get("title")]
    except Exception:
        return []