import os
import time
import threading

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import warnings
warnings.filterwarnings("ignore")

from core import ui
from core.listener import Listener
from core.brain import Brain
from core.speaker import Speaker
from core import memory
from config import LOG_DIR, USE_STREAMING, SHOW_TERMINAL_OUTPUT
from commands.router import handle as handle_command
from commands import conversation_skill

os.makedirs(LOG_DIR, exist_ok=True)

EXIT_WORDS = {"exit", "stop", "goodbye", "quit", "shut down", "shutdown"}

_stop_event = threading.Event()
_reminder_stop = threading.Event()

_UNKNOWN_PHRASES = [
    "i don't have information", "i don't have that information",
    "i don't have access to current", "i don't have access to real-time",
    "i don't have access to live",
    "i don't have the ability to retrieve", "i don't have the ability to access",
    "i don't have the ability to provide",
    "i cannot access current", "i can't access current",
    "i cannot retrieve", "i can't retrieve",
    "i'm unable to access", "i'm unable to retrieve",
    "i don't know the current",
    "my knowledge cutoff", "as of my last update", "as of my last training",
    "beyond my knowledge", "past my training data",
]


def _groq_says_unknown(reply: str) -> bool:
    lower = reply.lower()
    return any(p in lower for p in _UNKNOWN_PHRASES)


def reminder_worker(speaker):
    while not _reminder_stop.is_set():
        try:
            due = memory.get_due_reminders()
            for r in due:
                time.sleep(1)
                speaker.speak(f"Reminder: {r['text']}")
                memory.advance_reminder(r["id"])
        except Exception as e:
            if SHOW_TERMINAL_OUTPUT:
                print(f"[Reminder error] {e}")
        _reminder_stop.wait(30)


def announce_missed(speaker):
    missed = memory.get_missed_reminders(grace_minutes=5)
    if not missed:
        return
    names = ", ".join(r["text"] for r in missed)
    speaker.speak(
        f"While I was offline, you missed {len(missed)} reminder"
        f"{'s' if len(missed) > 1 else ''}: {names}."
    )
    for r in missed:
        memory.advance_reminder(r["id"])


def handle_groq_with_search(user_text, brain, speaker):
    reply = brain.think(user_text)
    if _groq_says_unknown(reply):
        ui.set_status("🌐 Browsing web...")
        reply = brain.think_with_search()
        if _groq_says_unknown(reply):
            reply = "I searched the web but couldn't find a reliable answer."
    speaker.speak(reply)


def assistant_loop(hud):
    ui.set_status("Loading Whisper...")
    listener = Listener()

    ui.set_status("Loading brain...")
    brain = Brain()

    ui.set_status("Loading Kokoro...")
    speaker = Speaker()

    # ← Wire up conversation skill with speaker + brain
    conversation_skill.set_dependencies(speaker, brain)

    ui.set_status("TRAVIS online")
    speaker.speak("TRAVIS system online. How can I assist you?")
    announce_missed(speaker)

    reminder_thread = threading.Thread(
        target=reminder_worker, args=(speaker,), daemon=True
    )
    reminder_thread.start()

    empty_count = 0

    try:
        while not _stop_event.is_set():
            ui.set_status("🎤 Listening...")
            user_input = listener.listen()

            if _stop_event.is_set():
                break

            if not user_input:
                if listener.push_to_talk:
                    continue
                empty_count += 1
                ui.set_status("😴 Idle")
                time.sleep(min(0.5 * empty_count, 5.0))
                continue

            empty_count = 0

            normalized = user_input.lower().strip().strip(" .,!?")
            if normalized in EXIT_WORDS:
                speaker.speak("Goodbye, Sir. Have a nice day.")
                break

            handled, reply = handle_command(user_input)

            if handled:
                ui.set_status("🔊 Speaking...")
                speaker.speak(reply)
            else:
                ui.set_status("🧠 Thinking...")
                if USE_STREAMING:
                    stream = brain.think_stream(user_input)
                    speaker.speak_stream(stream)
                else:
                    handle_groq_with_search(user_input, brain, speaker)

    except Exception as e:
        ui.set_status(f"⚠ Error: {e}")
        if SHOW_TERMINAL_OUTPUT:
            import traceback
            traceback.print_exc()
    finally:
        _stop_event.set()
        _reminder_stop.set()
        ui.set_status("Offline")


def main():
    if SHOW_TERMINAL_OUTPUT:
        print("=" * 50)
        print("  T.R.A.V.I.S  -  Initializing...")
        print("=" * 50)

    hud = ui.init_hud()

    assistant_thread = threading.Thread(
        target=assistant_loop, args=(hud,), daemon=True
    )
    assistant_thread.start()

    try:
        hud.run()
    except KeyboardInterrupt:
        pass

    _stop_event.set()
    _reminder_stop.set()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Interrupted by user]")
    except Exception as e:
        print(f"[Error] {e}")