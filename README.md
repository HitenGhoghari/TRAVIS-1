# T.R.A.V.I.S

> **T**extual **R**easoning **A**nd **V**oice **I**nteractive **S**ystem
> 
> A fully offline-first, privacy-respecting personal voice assistant built in Python.

TRAVIS is a Jarvis-inspired voice assistant that runs on your laptop. It listens to your voice, understands natural language, executes system commands, remembers your facts, sets reminders, and can answer any general question via an LLM — all while keeping your personal data on your machine.

---

## ✨ Features

- 🎤 **Accurate speech recognition** — Whisper (`faster-whisper`) handles accents, background noise, and natural speech far better than traditional engines
- 🗣️ **Natural voice synthesis** — Kokoro TTS produces human-sounding speech, fully offline after the first download
- 🧠 **Intelligent brain** — Groq (LLaMA / GPT-OSS) answers any free-form question with low latency
- ⚡ **Command router** — 30+ instant local skills run without touching the network
- 🎯 **Push-to-talk** — Microphone is only open while you hold `Ctrl+Space` (privacy-first)
- 💾 **Persistent memory** — Remember facts, save notes, schedule reminders
- ⏰ **Background reminders** — Alerts fire even while you're not talking to it
- 🔒 **Privacy-respecting** — Personal memory, notes, and reminders **never** leave your machine
- 🖥️ **Verified actions** — Opens apps only when confirmed; closes apps gracefully (preserves unsaved work)
- 🎛️ **Adaptive noise floor** — Works in quiet or noisy rooms without configuration

---

## 🎬 Demo

```
==================================================
  T.R.A.V.I.S  -  Initializing...
==================================================
🎤 Push-to-talk active. Hold CTRL+SPACE to speak.
TRAVIS: TRAVIS system online. How can I assist you?

🔴 Recording...  ⏹️  Processing...
You: Open Notepad
TRAVIS: Notepad is running.

🔴 Recording...  ⏹️  Processing...
You: Remember that my Wi-Fi password is unter2
TRAVIS: Got it. I'll remember that my wi-fi password is unter2.

🔴 Recording...  ⏹️  Processing...
You: Remind me to stretch in 20 minutes
TRAVIS: Reminder set: stretch. I'll alert you at 14:32.

🔴 Recording...  ⏹️  Processing...
You: Who is Saitama?
TRAVIS: Saitama is the bald hero of One-Punch Man, known for
defeating any opponent with a single punch...
```

---

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  EARS       │ →  │  ROUTER      │ →  │  MOUTH       │
│  Whisper    │    │  Skills?     │    │  Kokoro TTS  │
│  (STT)      │    │  ↓ no        │    │              │
└─────────────┘    │  Groq (LLM)  │    └──────────────┘
                   └──────────────┘
```

Every utterance flows through **four stages**:

1. **Listen** — Record audio → Whisper transcribes to text
2. **Route** — Skills run first (instant, offline); if no skill matches → **Brain**
3. **Think** — Groq generates a natural reply (only if needed)
4. **Speak** — Kokoro synthesizes and plays, sentence-by-sentence

Local **skills** (time, apps, memory, reminders) never call the network. Only free-form questions hit Groq.

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Speech-to-text** | `faster-whisper` (small) | Accurate, accent-robust, offline |
| **Brain** | Groq (`openai/gpt-oss-120b`) | Ultra-low latency, free tier |
| **Text-to-speech** | Kokoro 82M | Natural voice, offline after first use |
| **Audio I/O** | `sounddevice` | Cross-platform, low latency |
| **Hotkeys** | `keyboard` | Global push-to-talk on Windows |
| **Storage** | JSON files | Simple, inspectable, no DB needed |

---

## 📦 Installation

### Requirements

- **Python 3.10 – 3.12** (Python 3.13 has issues with Kokoro's dependency chain)
- **Windows 10/11** (Linux/macOS work with minor changes — see [#platform-notes](#-platform-notes))
- **~2 GB free disk space** (Whisper + Kokoro models, downloaded on first run)
- **A working microphone**

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/myjarvis.git
cd myjarvis

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate    # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the environment template
copy .env.example .env        # Windows
# cp .env.example .env        # Linux/macOS

# 5. Edit .env and add your Groq API key
# Get a free key at https://console.groq.com/keys

# 6. Run
python main.py
```

### Platform Notes

- **Windows**: Run the terminal **as Administrator** the first time (needed for `keyboard` to hook global hotkeys)
- **Linux/macOS**: `keyboard` needs `sudo` or a udev rule; `sounddevice` needs `portaudio` (`sudo apt install portaudio19-dev` / `brew install portaudio`)

---

## 🎮 Usage

### Push-to-talk (default)

Hold **`Ctrl+Space`** → speak → release. TRAVIS processes what you said.

The microphone is **closed** at all other times — no accidental recordings, no echo pickup.

### Always-listening mode

Set `INPUT_MODE = "vad"` in `config.py` if you prefer voice-activity detection (no hotkey needed).

### Example commands

| Say | What happens |
|-----|-------------|
| "What's the time?" | Instant reply |
| "What's today's date?" | Instant reply |
| "What's my battery?" | Instant reply |
| "Open Notepad" | Launches and verifies Notepad |
| "Close Chrome" | Asks Chrome to close (preserves unsaved tabs) |
| "Volume up" / "Mute" | Controls system volume |
| "Play lo-fi beats" | Opens YouTube and searches |
| "Take a screenshot" | Saves to `screenshot.png` |
| "Remember that X is Y" | Stores as a private fact |
| "What do you remember about X?" | Recalls the fact |
| "Remind me to stretch in 20 minutes" | Schedules a reminder |
| "Take a note: buy milk" | Appends to `notes.json` |
| "Who is Saitama?" | Routes to Groq (LLM) |

---

## 📁 Project Structure

```
myjarvis/
├── main.py                  # Entry point — orchestrator loop
├── config.py                # All settings in one place
├── requirements.txt         # Python dependencies
├── .env                     # Your secrets (git-ignored)
├── .env.example             # Template for new clones
│
├── core/
│   ├── listener.py          # Whisper STT + push-to-talk
│   ├── brain.py             # Groq LLM
│   ├── speaker.py           # Kokoro TTS
│   └── memory.py            # JSON storage engine
│
├── commands/
│   ├── router.py            # Dispatches utterances to skills
│   ├── system.py            # Time, date, battery, screenshot
│   ├── apps.py              # Open/close apps + websites
│   ├── media.py             # Volume, mute, YouTube play
│   └── memory_skill.py      # Remember, recall, notes, reminders
│
├── data/                    # Auto-created, git-ignored
│   ├── memory.json          # Private facts
│   ├── notes.json           # Free-form notes
│   └── reminders.json       # Scheduled alerts
│
├── models/                  # Auto-downloaded, git-ignored
├── logs/                    # Auto-created, git-ignored
└── venv/                    # Virtual environment, git-ignored
```

---

## 🔒 Privacy

TRAVIS is designed with **your data stays on your machine** as a first-class requirement.

| Data | Where it lives | Sent to Groq? |
|------|---------------|---------------|
| `data/memory.json` | Your disk | ❌ Never |
| `data/notes.json` | Your disk | ❌ Never |
| `data/reminders.json` | Your disk | ❌ Never |
| Your spoken question | — | ✅ Only this |
| Groq's reply | — | (comes back to you) |

The only thing Groq ever sees is the **raw text** of your free-form question. Local skills never touch the network.

---

## 🔧 Configuration

All tunables live in `config.py`:

| Setting | Default | What it does |
|---------|---------|-------------|
| `KOKORO_VOICE` | `"af_heart"` | TTS voice (`am_adam` = male, `af_heart` = female) |
| `KOKORO_SPEED` | `1.0` | Speech rate |
| `SILENCE_TIMEOUT` | `3.0` | Seconds of silence before stopping (VAD mode) |
| `INPUT_MODE` | `"ptt"` | `"ptt"` (push-to-talk) or `"vad"` (always-listening) |
| `PUSH_TO_TALK_HOTKEY` | `"ctrl+space"` | Hotkey for PTT mode |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | LLM used for reasoning |

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| `kokoro` install fails | Use **Python 3.10–3.12** (3.13 is unsupported by Kokoro 0.7.4) |
| `pyaudio` install fails | Windows: `pip install pipwin && pipwin install pyaudio` |
| Push-to-talk doesn't work | Run terminal as **Administrator** |
| Whisper is slow on first question | Already fixed — warm-up runs at startup |
| No mic detected | Check `sounddevice.query_devices()` |
| Kokoro is slow to start speaking | Normal on CPU; each sentence is streamed |

---

## 🗺️ Roadmap

- [x] Push-to-talk
- [x] Persistent memory
- [x] Reminders + background thread
- [x] Verified open / graceful close
- [x] Adaptive noise floor
- [ ] Recurring reminders
- [ ] Cancel reminders
- [ ] Wake word ("Hey Travis")
- [ ] Streaming Groq responses
- [ ] Weather skill
- [ ] GUI overlay

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [**Kokoro**](https://github.com/hexgrad/kokoro) by hexgrad — natural TTS
- [**faster-whisper**](https://github.com/SYSTRAN/faster-whisper) — fast speech recognition
- [**Groq**](https://groq.com) — ultra-low latency LLM inference
- [**Mark-LVI**](https://github.com/FatihMakes/Mark-LVI) by FatihMakes — architecture inspiration

---

## ⭐ If TRAVIS is useful, give it a star!