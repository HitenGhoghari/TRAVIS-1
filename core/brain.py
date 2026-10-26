import json
import os
import re

from groq import Groq

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    SYSTEM_PROMPT,
    ENABLE_MEMORY_RAG,
    ENABLE_BROWSER_SEARCH,
    ENABLE_PERSISTENT_HISTORY,
    MAX_PERSISTENT_MESSAGES,
    MAX_GROQ_CONTEXT,
    USER_REGION_NOTE,
    BASE_DIR,
)
from core import memory


CONVERSATION_FILE = os.path.join(BASE_DIR, "data", "conversation.json")

_STOPWORDS = {
    "what", "is", "my", "the", "a", "an", "do", "you", "know", "about",
    "tell", "me", "can", "i", "have", "of", "to", "in", "on", "for",
    "and", "or", "it", "this", "that", "with", "from", "how", "when",
    "where", "who", "which", "why", "are", "was", "were", "be", "been",
}


def _extract_keywords(text: str):
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _find_relevant_facts(user_text: str, max_facts: int = 5):
    if not ENABLE_MEMORY_RAG:
        return {}
    facts = memory.load_memory()
    if not facts:
        return {}
    query_words = _extract_keywords(user_text)
    if not query_words:
        return {}
    scored = []
    for key, value in facts.items():
        if value is True:
            continue
        key_words = _extract_keywords(key)
        overlap = len(query_words & key_words)
        if overlap > 0:
            scored.append((overlap, key, value))
    scored.sort(key=lambda x: x[0], reverse=True)
    return {k: v for _, k, v in scored[:max_facts]}


def _strip_citations(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"【[^】]*】", "", text)
    text = re.sub(r"\[\d+†[^\]]*\]", "", text)
    text = re.sub(r"\s*\[\d+\]\s*$", "", text)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


class Brain:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing. Check your .env file.")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Load persisted history
        for msg in self._load_history_from_disk():
            self.history.append(msg)

    # ---------- Persistence ----------
    def _load_history_from_disk(self):
        if not ENABLE_PERSISTENT_HISTORY:
            return []
        try:
            with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        if not isinstance(data, list):
            return []

        valid = []
        for m in data:
            if (isinstance(m, dict)
                    and m.get("role") in ("user", "assistant")
                    and isinstance(m.get("content"), str)):
                valid.append({"role": m["role"], "content": m["content"]})
        return valid[-MAX_PERSISTENT_MESSAGES:]

    def _save_history_to_disk(self):
        if not ENABLE_PERSISTENT_HISTORY:
            return
        try:
            os.makedirs(os.path.dirname(CONVERSATION_FILE), exist_ok=True)
            to_save = self.history[1:][-MAX_PERSISTENT_MESSAGES:]   # skip system prompt
            with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
                json.dump(to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[history save error] {e}")

    def clear_history(self):
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        try:
            if os.path.exists(CONVERSATION_FILE):
                os.remove(CONVERSATION_FILE)
        except Exception as e:
            print(f"[clear history error] {e}")

    def exchange_count(self):
        return sum(1 for m in self.history if m.get("role") == "user")

    # ---------- Message building ----------
    def _trim_history(self):
        if len(self.history) > MAX_PERSISTENT_MESSAGES + 1:
            self.history = [self.history[0]] + self.history[-MAX_PERSISTENT_MESSAGES:]

    def _build_messages(self):
        # Slice to last MAX_GROQ_CONTEXT messages (system prompt always kept)
        if len(self.history) > MAX_GROQ_CONTEXT + 1:
            messages = [self.history[0]] + self.history[-MAX_GROQ_CONTEXT:]
        else:
            messages = list(self.history)

        # Region note re-asserted every call
        messages.insert(1, {"role": "system", "content": USER_REGION_NOTE})

        last_user_idx = None
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "user":
                last_user_idx = i
                break

        if last_user_idx is not None:
            last_user_text = messages[last_user_idx]["content"]
            relevant = _find_relevant_facts(last_user_text)
            if relevant:
                fact_str = "; ".join(f"{k} = {v}" for k, v in relevant.items())
                messages.insert(last_user_idx, {
                    "role": "system",
                    "content": f"Relevant facts from the user's local memory: {fact_str}",
                })
        return messages

    def _call_groq(self, force_search: bool = False, stream: bool = False):
        kwargs = {
            "messages": self._build_messages(),
            "model": GROQ_MODEL,
        }
        if ENABLE_BROWSER_SEARCH:
            kwargs["tools"] = [{"type": "browser_search"}]
            kwargs["tool_choice"] = "required" if force_search else "auto"
        if stream:
            kwargs["stream"] = True
        return self.client.chat.completions.create(**kwargs)

    # ---------- Public ----------
    def think(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        self._trim_history()
        try:
            response = self._call_groq(force_search=False, stream=False)
            raw = response.choices[0].message.content or ""
            reply = _strip_citations(raw)
            self.history.append({"role": "assistant", "content": reply})
            self._save_history_to_disk()
            return reply
        except Exception as e:
            print(f"[Groq Error] {e}")
            return "Sorry, I couldn't reach my brain right now."

    def think_with_search(self) -> str:
        while self.history and self.history[-1]["role"] == "assistant":
            self.history.pop()
        try:
            response = self._call_groq(force_search=True, stream=False)
            raw = response.choices[0].message.content or ""
            reply = _strip_citations(raw)
            self.history.append({"role": "assistant", "content": reply})
            self._save_history_to_disk()
            return reply
        except Exception as e:
            print(f"[Groq search error] {e}")
            return "I tried to search the web, but couldn't reach my brain right now."

    def think_stream(self, user_text: str):
        self.history.append({"role": "user", "content": user_text})
        self._trim_history()
        try:
            stream = self._call_groq(force_search=False, stream=True)
            full = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full += delta
                    yield _strip_citations(delta) or ""
            self.history.append({"role": "assistant", "content": _strip_citations(full)})
            self._save_history_to_disk()
        except Exception as e:
            print(f"[Groq Error] {e}")
            yield "Sorry, I couldn't reach my brain right now."