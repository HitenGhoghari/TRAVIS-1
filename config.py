import os
from dotenv import load_dotenv

load_dotenv()

# ---------- API Keys ----------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# ---------- Voice Engine ----------
# "kokoro" → jf_alpha (your favourite)
# "piper"  → dual voice (alba + alan)
VOICE_ENGINE = "kokoro"

# ----- Kokoro (used when VOICE_ENGINE = "kokoro") -----
KOKORO_LANG = "a"              # 'a' = American English phonemizer
KOKORO_VOICE = "jf_alpha"      # Japanese female — speaks English beautifully
KOKORO_SAFETY_VOICE = "jf_alpha"   # same voice for safety (or use "am_adam")
KOKORO_SPEED = 1.0

# ----- Piper (used when VOICE_ENGINE = "piper") -----
PIPER_VOICE = "en_US-lessac-medium"
PIPER_SAFETY_VOICE = "en_US-ryan-high"
PIPER_LENGTH_SCALE = 1.10

# ---------- Pauses ----------
SPAN_PAUSE_SECONDS = 0.25

# ---------- Emotion → speed ----------
EMOTION_SPEED = {
    "neutral":   1.00,
    "happy":     1.00,
    "sad":       0.92,
    "angry":     1.00,
    "excited":   1.03,
    "disgust":   0.96,
    "sarcastic": 0.98,
    "surprised": 1.02,
}

# ---------- Input Mode ----------
INPUT_MODE = "ptt"
PUSH_TO_TALK_HOTKEY = "ctrl+space"
SILENCE_TIMEOUT = 3.0

# ---------- Region ----------
USER_COUNTRY = "India"
USER_CURRENCY = "INR"
USER_CURRENCY_SYMBOL = "₹"
USER_REGION_NOTE = (
    "The user lives in India. Always use Indian context: "
    "Indian Rupees (INR, ₹), metric units, Indian English, "
    "Indian news and sports, and Indian numbering (lakh, crore) where natural. "
    "Do not assume US or UK context."
)

# ---------- Weather ----------
HOME_CITY = "Surat"
HOME_COUNTRY = "IN"
USE_IP_LOCATION = False
WEATHER_UNITS = "metric"

# ---------- News ----------
NEWS_COUNTRY_CODE = "in"
NEWS_TOPIC_INDIA_BIAS = False
NEWS_MAX_SEEN = 300

# ---------- UI ----------
SHOW_TERMINAL_OUTPUT = False

# ---------- Memory / Privacy ----------
ENABLE_MEMORY_RAG = True

# ---------- Persistent Conversation ----------
ENABLE_PERSISTENT_HISTORY = True
MAX_PERSISTENT_MESSAGES = 200
MAX_GROQ_CONTEXT = 40

# ---------- Persona & Dialogue ----------
PERSONA_FILE = os.path.join(BASE_DIR, "data", "persona.json")
ENABLE_DIALOGUE_MANAGER = True
ENABLE_EMOTION_TAGS = True

# ---------- Morning Briefing ----------
ENABLE_MORNING_BRIEFING = True   # Set to False to skip briefing entirely

# ---------- Groq Settings ----------
GROQ_MODEL = "openai/gpt-oss-120b"
USE_STREAMING = False
ENABLE_BROWSER_SEARCH = True

SYSTEM_PROMPT = (
    "You are TRAVIS, a personal AI assistant built to feel like a trusted "
    "colleague rather than a customer-service bot. You speak aloud through "
    "text-to-speech, so your words must sound natural when heard, not read. "
    "\n\n"
    "VOICE RULES:\n"
    "- Begin replies with a short natural opener: 'Right', 'Got it', 'Okay', "
    "'Hm', 'So'.\n"
    "- Use discourse markers sparingly.\n"
    "- Mirror the user's energy.\n"
    "- NEVER use bullet points, numbered lists, markdown, code blocks, or "
    "newlines.\n"
    "- Keep most answers to 1-3 sentences unless the user asks for detail.\n"
    "- Ask at most one clarifying question.\n"
    "\n"
    "EMOTION TAGGING RULES:\n"
    "- Prefix EVERY sentence with exactly ONE emotion tag in square brackets.\n"
    "- Allowed tags: [neutral], [happy], [sad], [angry], [excited], "
    "[disgust], [sarcastic], [surprised].\n"
    "- The tag must be the first token of the sentence.\n"
    "- Do not explain or mention the tags.\n"
    "\n"
    "HONESTY RULES:\n"
    "- Never say 'As an AI'.\n"
    "- You cannot directly control the user's device. If asked, say 'I can't do that'.\n"
    "- If you do not know something, say so and offer to search.\n"
    "\n"
    f"REGION CONTEXT:\n{USER_REGION_NOTE}\n"
    "When reporting prices, convert to Indian Rupees where possible.\n"
)