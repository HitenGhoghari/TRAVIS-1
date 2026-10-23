import os
from dotenv import load_dotenv

load_dotenv()

# ---------- API Keys ----------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# ---------- Voice Settings ----------
KOKORO_LANG = "a"
KOKORO_VOICE = "af_heart"
KOKORO_SPEED = 1.0
SILENCE_TIMEOUT = 3.0

# ---------- Input Mode ----------
# "ptt" = push-to-talk (hold Ctrl+Space)   ← recommended
# "vad" = voice activity detection (always listening)
INPUT_MODE = "ptt"
PUSH_TO_TALK_HOTKEY = "ctrl+space"

# ---------- Groq Settings ----------
GROQ_MODEL = "openai/gpt-oss-120b"
SYSTEM_PROMPT = (
    "You are TRAVIS, a helpful, concise personal assistant. "
    "Your responses are spoken aloud through text-to-speech, so ALWAYS respond "
    "in natural, flowing sentences only. "
    "NEVER use bullet points, numbered lists, markdown, code blocks, or newlines. "
    "Keep every answer to 1-3 sentences. If asked what you can do, summarize "
    "your capabilities in one short paragraph — never as a list."
)