# T.R.A.V.I.S — v1.1 (Stable 1.x Release)

> ⚠️ **You are viewing TRAVIS v1.1** — the final stable version of the 1.x line.
>
> **Looking for the latest?** → [**TRAVIS v2.0 on main**](https://github.com/YOUR_USERNAME/myjarvis)

[![Version: v1.1](https://img.shields.io/badge/version-1.1.0-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6.svg)]()

A privacy-respecting personal voice assistant for Windows — 88 commands across 11 skill modules, built on Whisper (STT), Kokoro (TTS), and Groq (LLM).

---

## 🆚 Which Version Should I Use?

| Version | Status | Description |
|---|---|---|
| **v2.0** | ⭐ **Recommended** | Adds personality engine, dual-voice emotion, episodic memory, adaptive verbosity, morning briefing. [Get v2.0 →](https://github.com/YOUR_USERNAME/myjarvis) |
| **v1.1** | Stable 1.x | This release — 88 commands, single voice, no personality layer. Simple and reliable. |

---

## ✨ What's in v1.1

### Voice
- Speech recognition via `faster-whisper` (accent-robust, offline)
- Natural TTS via Kokoro
- Push-to-talk (`Ctrl+Space`)
- Adaptive noise floor

### Brain
- Groq LLM (`openai/gpt-oss-120b`) for free-form questions
- Browser search tool for live data
- Persistent conversation history across restarts

### Skills (88 commands, 11 modules)
- 🌤️ **Weather** (current, rain, forecast, air quality)
- 📰 **News** (India-focused Google News RSS)
- ⏰ **Reminders** (one-time, daily, weekly, monthly, interval, cancellable)
- ⏱️ **Timers** (set, cancel, list)
- 📋 **Clipboard** (read, copy, save as note, clear)
- 🕐 **Time, date, day**
- 🔋 **Battery, system info**
- 🖥️ **Screenshots**
- 💡 **Brightness** (up, down, set N)
- 🔒 **Lock, sleep, restart, shutdown** (with 60s+ cancel window)
- 🗑️ **Empty recycle bin**
- 🎵 **Volume, mute, unmute, next/prev, play/pause**
- 🚀 **Apps:** open/close Chrome, Notepad, Calculator, Explorer, YouTube, Google, GitHub
- 📝 **Notes** (add, list)
- 🌐 **YouTube playback**
- 🔐 **Memory** (remember, recall)
- 🆔 **Self-audit** ("what can you do?")

### Presence
- Animated HUD overlay with chat log
- Push-to-talk mic (closed when not recording)

---

## 📦 Installation

### Requirements
- **Python 3.10 – 3.12** (3.13 has issues with Kokoro)
- **Windows 10/11**
- **~2 GB free disk space** (models downloaded on first run)
- **Working microphone**
- **Groq API key** (free at [console.groq.com/keys](https://console.groq.com/keys))

### Steps

```bash
# 1. Clone the v1.1 tag
git clone -b v1.1 [https://github.com/YOUR_USERNAME/myjarvis.git](https://github.com/YOUR_USERNAME/myjarvis.git)
cd myjarvis

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Environment template
copy .env.example .env
# Edit .env and add your GROQ_API_KEY

# 5. Run
python main.py
```

---

## 🎮 Example Commands

| Say | What happens |
|---|---|
| *"What's the weather in Mumbai?"* | Current weather |
| *"What's the news?"* | Fresh Indian headlines |
| *"Tell me about black holes"* | Groq answer |
| *"Remember that my Wi-Fi password is X"* | Stored locally |
| *"Remind me to stretch in 20 minutes"* | Reminder scheduled |
| *"Open Notepad"* | Launches Notepad |
| *"Restart computer"* | 120s warning; "cancel" aborts |
| *"What can you do?"* | Lists skill count |

---

## 🔒 Privacy

Your `data/memory.json`, `notes.json`, and `reminders.json` never leave your machine. Only the current question goes to Groq.

---

## 🚀 Upgrading to v2.0

```bash
git checkout main
git pull origin main
pip install -r requirements.txt
```

Your existing `data/` files (memory, notes, reminders, conversation) are fully compatible — no migration needed.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

⭐ If TRAVIS is useful, give it a star!