import os
from dotenv import load_dotenv

load_dotenv()

# ---------- API Keys ----------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# ---------- Voice Settings ----------
KOKORO_LANG = "a"
KOKORO_VOICE = "af_heart"
KOKORO_SPEED = 1.0
SILENCE_TIMEOUT = 3.0   # VAD mode only — ignored in PTT

# ---------- Input Mode ----------
INPUT_MODE = "ptt"
PUSH_TO_TALK_HOTKEY = "ctrl+space"

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
MAX_PERSISTENT_MESSAGES = 200    # ~100 exchanges stored on disk
MAX_GROQ_CONTEXT = 40            # last ~20 exchanges sent to Groq per call

# ---------- Groq Settings ----------
GROQ_MODEL = "openai/gpt-oss-120b"
USE_STREAMING = False
ENABLE_BROWSER_SEARCH = True

SYSTEM_PROMPT = (
    "You are TRAVIS, a helpful, concise personal assistant. "
    "Your responses are spoken aloud through text-to-speech, so ALWAYS respond "
    "in natural, flowing sentences only. "
    "NEVER use bullet points, numbered lists, markdown, code blocks, or newlines. "
    "Keep every answer to 1-3 sentences. If asked what you can do, summarize "
    "your capabilities in one short paragraph — never as a list. "
    f"{USER_REGION_NOTE} "
    "When reporting prices, convert to Indian Rupees (INR, ₹) where possible. "
    "For gold, search for the current gold rate in India per 10 grams and answer "
    "in INR per 10 grams, not USD per troy ounce. "
    "You have access to a live browser search tool. When the user asks about "
    "current prices, live news, today's events, sports scores, stock prices, "
    "or anything requiring real-time information, use the browser search tool. "
    "Prefer Indian sources and Indian context for news, sports, and prices. "
    "IMPORTANT: You cannot directly control the user's device or applications. "
    "You cannot unmute, adjust brightness, change WiFi, or perform physical "
    "actions. If asked, clearly say 'I can't do that'. NEVER claim to have "
    "performed an action you didn't."
)