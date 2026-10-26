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
    ENABLE_EMOTION_TAGS,
    MAX_PERSISTENT_MESSAGES,
    MAX_GROQ_CONTEXT,
    USER_REGION_NOTE,
    PERSONA_FILE,
    ENABLE_DIALOGUE_MANAGER,
    BASE_DIR,
)
from core import memory
from core import relationship
from core import episodes as episodes_mod
from core.dialogue import classify_posture, posture_note, classify_emotion_local
from core.emotions import TAG_RE


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


def _ensure_emotion_tags(text: str, posture: str) -> str:
    if not ENABLE_EMOTION_TAGS:
        return text
    if TAG_RE.search(text):
        return text
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    tagged = []
    for p in parts:
        if not p.strip():
            continue
        emo = classify_emotion_local(p, posture)
        tagged.append(f"[{emo}] {p.strip()}")
    return " ".join(tagged) if tagged else text


class Brain:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing. Check your .env file.")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.persona = self._load_persona()

        for msg in self._load_history_from_disk():
            self.history.append(msg)

        # Session tracking
        self.session_start_index = len(self.history)
        self._session_summarized = False

    # ---------- Persona ----------
    def _load_persona(self):
        try:
            with open(PERSONA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _persona_note(self) -> str:
        if not self.persona:
            return ""
        style = self.persona.get("speech_style", {})
        traits = ", ".join(self.persona.get("core_traits", []))

        rdata = relationship.load_relationship()
        address = rdata.get("preferred_name", "Sir")
        trust = int(rdata.get("trust_level", 1))
        sessions = int(rdata.get("session_count", 0))
        days = relationship.get_days_known()

        prefs = rdata.get("learned_preferences", {})
        verbosity = int(prefs.get("verbosity", 3))

        formality = style.get("formality", 0.6)
        humor = style.get("humor", 0.5)
        warmth = style.get("warmth", 0.4)

        if trust <= 3:
            trust_hint = "Be formal and respectful — the relationship is new."
        elif trust >= 7:
            trust_hint = "Be relaxed and conversational — this is a trusted, long relationship."
        else:
            trust_hint = "Be warm but composed."

        if verbosity <= 2:
            verbosity_hint = (
                "Extreme brevity: answer in ONE short sentence. "
                "No preamble, no filler, no context. Just the essential fact."
            )
        elif verbosity <= 4:
            verbosity_hint = (
                "Concise: one or two sentences with the key point. "
                "Skip examples unless essential."
            )
        elif verbosity <= 6:
            verbosity_hint = (
                "Moderate: two or three sentences with useful detail."
            )
        elif verbosity <= 8:
            verbosity_hint = (
                "Detailed: a full paragraph with context and one example."
            )
        else:
            verbosity_hint = (
                "Comprehensive: multiple paragraphs, thorough explanation, "
                "include context, examples, and edge cases."
            )

        return (
            f"Persona: {traits}. Address the user as '{address}'. "
            f"Formality {formality:.1f}, humor {humor:.1f}, warmth {warmth:.1f}. "
            f"Relationship: trust {trust}/10, {sessions} sessions, {days} days known. "
            f"Verbosity preference: {verbosity}/10 — {verbosity_hint} "
            f"{trust_hint} "
            "Keep persona subordinate to usefulness."
        )

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
            to_save = self.history[1:][-MAX_PERSISTENT_MESSAGES:]
            with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
                json.dump(to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[history save error] {e}")

    def clear_history(self):
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.session_start_index = len(self.history)
        try:
            if os.path.exists(CONVERSATION_FILE):
                os.remove(CONVERSATION_FILE)
        except Exception as e:
            print(f"[clear history error] {e}")

    def exchange_count(self):
        return sum(1 for m in self.history if m.get("role") == "user")

    # ---------- Session summarization ----------
    def summarize_session(self):
        """Called at shutdown. Saves a one-sentence summary to episodes.json."""
        if self._session_summarized:
            print("[summarize] already done, skipping")
            return

        print(f"[summarize] start: start_idx={self.session_start_index}, "
              f"history_len={len(self.history)}")

        if self.session_start_index is None:
            print("[summarize] no session_start_index — skipping")
            self._session_summarized = True
            return

        session_msgs = self.history[self.session_start_index:]
        print(f"[summarize] session messages: {len(session_msgs)}")

        if len(session_msgs) < 2:
            print("[summarize] session too short — skipping")
            self._session_summarized = True
            return

        lines = []
        for m in session_msgs:
            role = "User" if m["role"] == "user" else "TRAVIS"
            content = TAG_RE.sub("", m["content"]).strip()
            if content:
                lines.append(f"{role}: {content}")

        if not lines:
            print("[summarize] no non-empty messages — skipping")
            self._session_summarized = True
            return

        conv_text = "\n".join(lines)
        if len(conv_text) > 3000:
            conv_text = conv_text[-3000:]

        summary = None
        try:
            print("[summarize] calling Groq...")
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You summarize conversations for a personal AI assistant. "
                            "Respond with ONE sentence under 40 words. "
                            "Focus on: what the user asked about, tasks completed, "
                            "and facts learned. No greetings, no formatting, no quotes."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Summarize:\n\n{conv_text}",
                    },
                ],
                model=GROQ_MODEL,
                max_tokens=800,   # generous budget — reasoning models use tokens internally
            )
            choice = response.choices[0]
            finish_reason = getattr(choice, "finish_reason", "?")
            summary = (choice.message.content or "").strip()
            summary = _strip_citations(summary)
            print(f"[summarize] groq returned: {summary[:100]!r} "
                  f"(finish={finish_reason})")
        except Exception as e:
            print(f"[summarize groq error] {e}")

        if not summary:
            greetings = {
                "hello", "hi", "hey", "how are you", "how are you?",
                "good morning", "good evening", "good night",
            }
            user_msgs = []
            for m in session_msgs:
                if m["role"] != "user":
                    continue
                content = TAG_RE.sub("", m["content"]).strip().strip(" .,!?")
                if not content or content.lower() in greetings or len(content) < 4:
                    continue
                user_msgs.append(content[:80])

            if user_msgs:
                topics = "; ".join(user_msgs[:3])
                summary = f"Session topics: {topics}"
                print("[summarize] using fallback from user messages")
            else:
                summary = f"Brief social exchange ({len(session_msgs)} messages)"
                print("[summarize] using generic fallback")

        if summary:
            ep = episodes_mod.add_episode(summary, len(session_msgs))
            if ep:
                print(f"[episodes] Saved ({len(session_msgs)} msgs): {summary[:100]}")
            else:
                print("[episodes] add_episode returned None")
        else:
            print("[summarize] no summary produced — nothing saved")

        self._session_summarized = True

    # ---------- Message building ----------
    def _trim_history(self):
        if len(self.history) > MAX_PERSISTENT_MESSAGES + 1:
            self.history = [self.history[0]] + self.history[-MAX_PERSISTENT_MESSAGES:]

    def _build_messages(self, user_text: str):
        if len(self.history) > MAX_GROQ_CONTEXT + 1:
            messages = [self.history[0]] + self.history[-MAX_GROQ_CONTEXT:]
        else:
            messages = list(self.history)

        # 1. Region
        messages.insert(1, {"role": "system", "content": USER_REGION_NOTE})

        # 2. Recent episodes
        episode_note = episodes_mod.recent_for_prompt(3)
        if episode_note:
            messages.insert(2, {"role": "system", "content": episode_note})

        # 3. Persona — insert BEFORE last user message
        persona_note = self._persona_note()
        if persona_note:
            last_user_idx = None
            for i in range(len(messages) - 1, -1, -1):
                if messages[i]["role"] == "user":
                    last_user_idx = i
                    break
            if last_user_idx is not None:
                messages.insert(last_user_idx, {"role": "system", "content": persona_note})
            else:
                messages.append({"role": "system", "content": persona_note})

        # 4. Posture — insert BEFORE last user message
        if ENABLE_DIALOGUE_MANAGER:
            posture = classify_posture(user_text)
            last_user_idx = None
            for i in range(len(messages) - 1, -1, -1):
                if messages[i]["role"] == "user":
                    last_user_idx = i
                    break
            if last_user_idx is not None:
                messages.insert(last_user_idx, {
                    "role": "system",
                    "content": posture_note(posture),
                })

        # 5. Memory facts (before last user message)
        last_user_idx = None
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "user":
                last_user_idx = i
                break

        if last_user_idx is not None:
            relevant = _find_relevant_facts(messages[last_user_idx]["content"])
            if relevant:
                fact_str = "; ".join(f"{k} = {v}" for k, v in relevant.items())
                messages.insert(last_user_idx, {
                    "role": "system",
                    "content": f"Relevant facts from the user's local memory: {fact_str}",
                })
        return messages

    def _call_groq(self, user_text: str, force_search: bool = False, stream: bool = False):
        kwargs = {
            "messages": self._build_messages(user_text),
            "model": GROQ_MODEL,
            "temperature": 1,
            "max_tokens": 2048,          # ← Groq SDK 0.11.x uses max_tokens, not max_completion_tokens
        }
        if ENABLE_BROWSER_SEARCH:
            kwargs["tools"] = [{"type": "browser_search"}]
            kwargs["tool_choice"] = "required" if force_search else "auto"
        if stream:
            kwargs["stream"] = True

        try:
            return self.client.chat.completions.create(**kwargs)
        except Exception as e:
            err = str(e).lower()
            if ENABLE_BROWSER_SEARCH and (
                "output_parse_failed" in err
                or "failed_generation" in err
                or "tool_use_failed" in err
            ):
                print("[Groq] browser search failed — retrying without tools")
                kwargs.pop("tools", None)
                kwargs.pop("tool_choice", None)
                return self.client.chat.completions.create(**kwargs)
            raise

    def think(self, user_text: str) -> str:
        posture = classify_posture(user_text)
        self.history.append({"role": "user", "content": user_text})
        self._trim_history()

        try:
            response = self._call_groq(user_text, force_search=False, stream=False)
            raw = response.choices[0].message.content or ""
            reply = _strip_citations(raw)
            reply = _ensure_emotion_tags(reply, posture)
            self.history.append({"role": "assistant", "content": reply})
            self._save_history_to_disk()
            return reply
        except Exception as e:
            print(f"[Groq Error] {e}")
            return "[neutral] Sorry, I couldn't reach my brain right now."

    def think_with_search(self, user_text: str) -> str:
        posture = classify_posture(user_text)
        while self.history and self.history[-1]["role"] == "assistant":
            self.history.pop()

        try:
            response = self._call_groq(user_text, force_search=True, stream=False)
            raw = response.choices[0].message.content or ""
            reply = _strip_citations(raw)
            reply = _ensure_emotion_tags(reply, posture)
            self.history.append({"role": "assistant", "content": reply})
            self._save_history_to_disk()
            return reply
        except Exception as e:
            print(f"[Groq search error] {e} — falling back to normal reply")
            try:
                response = self._call_groq(user_text, force_search=False, stream=False)
                raw = response.choices[0].message.content or ""
                reply = _strip_citations(raw)
                reply = _ensure_emotion_tags(reply, posture)
                self.history.append({"role": "assistant", "content": reply})
                self._save_history_to_disk()
                return reply
            except Exception as e2:
                print(f"[Groq fallback error] {e2}")
                return "[neutral] I tried to search the web, but couldn't reach my brain right now."

    def think_stream(self, user_text: str):
        posture = classify_posture(user_text)
        self.history.append({"role": "user", "content": user_text})
        self._trim_history()

        try:
            stream = self._call_groq(user_text, force_search=False, stream=True)
            full = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full += delta
                    yield _strip_citations(delta) or ""
            full = _strip_citations(full)
            full = _ensure_emotion_tags(full, posture)
            self.history.append({"role": "assistant", "content": full})
            self._save_history_to_disk()
        except Exception as e:
            print(f"[Groq Error] {e}")
            yield "[neutral] Sorry, I couldn't reach my brain right now."