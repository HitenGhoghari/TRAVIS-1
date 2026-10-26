# T.R.A.V.I.S

> **T**extual **R**easoning **A**nd **V**oice **I**nteractive **S**ystem
>
> A privacy-respecting personal AI assistant with a personality — dual-voice emotion, episodic memory, and morning briefings.

[![Version](https://img.shields.io/badge/version-2.0.0-00e5ff.svg)](https://github.com/HitenGhoghari/myjarvis/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6.svg)]()
[![Status: Active](https://img.shields.io/badge/status-active-success.svg)]()

---

## 🆕 Two Versions Available

| Version | Release | Description |
|---|---|---|
| ⭐ **TRAVIS 2** *(recommended)* | [**v2.0**](https://github.com/HitenGhoghari/myjarvis/releases/tag/v2.0) | Personality engine, dual-voice emotion, episodic memory, morning briefing, adaptive verbosity |
| TRAVIS 1 *(stable baseline)* | [v1.1](https://github.com/HitenGhoghari/myjarvis/releases/tag/v1.1) | Working assistant: 88 commands, single voice, no personality layer |

**Get TRAVIS 2** (default — the `main` branch):

```bash
git clone [https://github.com/HitenGhoghari/myjarvis.git](https://github.com/HitenGhoghari/myjarvis.git)
```

**Get TRAVIS 1.1:**

```bash
git clone -b v1.1 [https://github.com/HitenGhoghari/myjarvis.git](https://github.com/HitenGhoghari/myjarvis.git)
```

---

## 🚀 What's New in v2.0

TRAVIS 2 isn't just more features — it's a qualitative shift from *"an assistant that works"* to *"an assistant that knows you."*

### 🎭 Personality Engine
- **Persistent persona (`persona.json`)** — traits, tone, boundaries survive restarts
- **Dialogue manager** — social / task / safety posture classification
- **Conversational naturalness** — natural openers (*"Right"*, *"Got it"*), discourse markers

### 🎙️ Emotional Voice
- **Dual voices** — warm female for social/task, firm male for safety
- **OR** — Kokoro `jf_alpha` if you prefer that timbre
- **Per-sentence emotion tags** — speed modulation and pause rhythm

### 🧠 Memory Layers
- **Conversation memory** — persistent across restarts
- **Episode memory** — session summaries injected into next session
- **Relationship memory** — trust level, sessions count, learned preferences

### 🎯 Adaptive Intelligence
- **Adaptive verbosity** — *"too long"* / *"more detail from now on"* permanently adjusts answers
- **Morning briefing** — first launch of the day: greeting + weather + news + reminders
- **Browser search** — native Groq `browser_search` tool

### 🛡️ Safety
- **3-layer shutdown safety** — 120s window, broad cancel patterns, defensive exit
- **Honest failure** — admits *"I can't do that"* instead of faking success

---

## ✨ Full Feature List

### Voice
- 🎤 **Speech recognition** — `faster-whisper` (offline)
- 🗣️ **Natural TTS** — Piper or Kokoro
- 🎯 **Push-to-talk** (`Ctrl+Space`)
- 🎛️ **Adaptive noise floor**

### Brain
- 🧠 **Groq LLM** (`openai/gpt-oss-120b`)
- 🌐 **Browser search tool**
- 🎭 **Persona layer** with trust-adaptive formality
- 🎯 **Posture router** (social / task / safety)

### Memory
- 💾 **Conversation history** (persists)
- 📚 **Episode memory** (session summaries)
- 👤 **Relationship memory** (trust, sessions, preferences)
- 🔐 **Local RAG** (only relevant facts sent to Groq)

### Skills (88 commands, 11 modules)
Weather, news, reminders (all recurrences), timers, clipboard, time/date, battery, screenshots, brightness, lock/sleep/restart, empty recycle bin, volume/mute/media, apps, notes, web search, YouTube, self-audit.

---

## 📦 Installation

### Requirements
- **Python 3.10 – 3.12**
- **Windows 10/11**
- **~2 GB free disk**
- **Working microphone**
- **Groq API key** (free at [console.groq.com/keys](https://console.groq.com/keys))

### Steps

```bash
# 1. Clone (v2.0 is on main)
git clone [https://github.com/HitenGhoghari/myjarvis.git](https://github.com/HitenGhoghari/myjarvis.git)
cd myjarvis

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Environment
copy .env.example .env
# Edit .env and add GROQ_API_KEY

# 5. Persona template
mkdir data
copy docs\persona.example.json data\persona.json

# 6. Run
python main.py
```

*First launch downloads Whisper (~466 MB) and TTS models (~330 MB). Subsequent launches are instant.*

---

## 🎮 Example Commands

| Say | What happens |
|---|---|
| *"What's the weather in Mumbai?"* | Current weather (INR / metric) |
| *"What's the news?"* | Fresh Indian headlines |
| *"Tell me about black holes"* | Groq + browser search if needed |
| *"Remember that my Wi-Fi password is X"* | Stored locally |
| *"Remind me to stretch every day at 8 AM"* | Recurring reminder |
| *"Too long"* | Verbosity drops permanently |
| *"More detail from now on"* | Verbosity rises permanently |
| *"Restart computer"* | 120s warning; *"cancel"* / *"stop"* aborts |
| *"What did we talk about last time?"* | References episode summaries |
| *"What can you do?"* | Enumerates skills |

---

## 🏗️ Architecture

```text
┌────────────┐   ┌──────────────────┐   ┌────────────┐
│  Whisper   │ → │  Router +        │ → │  TTS       │
│  (STT)     │   │  Dialogue        │   │  (dual     │
│            │   │  Manager         │   │   voice +  │
└────────────┘   │  ↓               │   │   emotion) │
                 │  Skills          │   └────────────┘
                 │  ↓ (no match)    │
                 │  Groq LLM        │
                 │  (+ browser)     │
                 └──────────────────┘
                        ↓
                 ┌──────────────────┐
                 │  Memory Layers   │
                 │  conversation /  │
                 │  episodes /      │
                 │  relationship    │
                 └──────────────────┘
```

---

## 📁 Project Structure

```text
myjarvis/
├── main.py                  # Orchestrator loop
├── config.py                # All settings
├── requirements.txt
├── .env                     # Your secrets (git-ignored)
├── .env.example             # Template
├── docs/
│   └── persona.example.json # Persona template
│
├── core/
│   ├── listener.py          # Whisper STT
│   ├── brain.py             # Groq LLM
│   ├── speaker.py           # TTS
│   ├── dialogue.py          # Posture classifier
│   ├── emotions.py          # Tag parser
│   ├── memory.py            # JSON storage
│   ├── relationship.py      # Trust / sessions
│   ├── episodes.py          # Session summaries
│   ├── preferences.py       # Verbosity detection
│   ├── briefing.py          # Morning briefing
│   └── ui.py                # HUD
│
├── commands/
│   ├── router.py            # Dispatch + safety
│   ├── about.py
│   ├── conversation_skill.py
│   ├── memory_skill.py
│   ├── system.py
│   ├── weather.py
│   ├── news.py
│   ├── timer_skill.py
│   ├── clipboard_skill.py
│   ├── apps.py
│   └── media.py
│
└── data/                    # Auto-created, git-ignored
    ├── memory.json
    ├── notes.json
    ├── reminders.json
    ├── conversation.json
    ├── episodes.json
    ├── relationship.json
    └── seen_news.json
```

---

## 🔒 Privacy

| Data | Where it lives | Sent to Groq? |
|---|---|---|
| `data/memory.json` | Your disk | ❌ Never (only matching facts) |
| `data/notes.json` | Your disk | ❌ Never |
| `data/reminders.json` | Your disk | ❌ Never |
| `data/conversation.json` | Your disk | ⚠️ Last 20 exchanges |
| `data/episodes.json` | Your disk | ⚠️ Last 3 summaries |

**Zero Data Retention:** Enable at [console.groq.com/settings/data-controls](https://console.groq.com/settings/data-controls).

---

## 🔧 Configuration

All settings in `config.py`:

| Setting | Default | Effect |
|---|---|---|
| `VOICE_ENGINE` | `"kokoro"` | `"kokoro"` or `"piper"` |
| `KOKORO_VOICE` | `"jf_alpha"` | Kokoro voice pack |
| `PIPER_VOICE` | `"en_US-lessac-medium"` | Piper social voice |
| `PIPER_SAFETY_VOICE` | `"en_US-ryan-high"` | Piper safety voice |
| `INPUT_MODE` | `"ptt"` | `"ptt"` or `"vad"` |
| `ENABLE_MORNING_BRIEFING` | `True` | Disable to skip briefing |
| `HOME_CITY` | `"Surat"` | Default weather city |
| `USE_STREAMING` | `False` | Enable LLM streaming |

---

## 🐛 Troubleshooting

| Issue | Fix |
|---|---|
| Kokoro crashes on install | Use Python 3.10–3.12 |
| Push-to-talk doesn't work | Run terminal as Administrator |
| First reply is very slow | Whisper warm-up runs at startup |
| Silent speech mid-reply | Check terminal for `[audio warning]` |
| Briefing didn't fire | Only fires on the first launch of the day |

---

## 🗺️ Roadmap

### v2.0 ✅
- [x] Personality engine + dialogue manager
- [x] Dual voice + emotion tags
- [x] Episodic memory
- [x] Relationship memory
- [x] Adaptive verbosity
- [x] Morning briefing
- [x] 3-layer shutdown safety

### v2.1 (planned)
- [ ] Gmail + Google Calendar via Groq MCP
- [ ] Streaming enabled by default
- [ ] Proactive reminder warnings
- [ ] System tray icon

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements
- **Kokoro** — natural TTS
- **Piper** — fast local TTS
- **faster-whisper** — speech recognition
- **Groq** — LLM inference
- **Mark-LVI** — architecture inspiration

⭐ If TRAVIS is useful, give it a star!