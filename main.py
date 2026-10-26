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
from core import relationship
from core import preferences
from core import briefing as briefing_mod
from core.dialogue import classify_posture
from config import (
    LOG_DIR, USE_STREAMING, SHOW_TERMINAL_OUTPUT, ENABLE_MORNING_BRIEFING,
)
from commands.router import handle as handle_command
from commands import conversation_skill

os.makedirs(LOG_DIR, exist_ok=True)

EXIT_WORDS = {
    "exit", "goodbye", "quit",
    "bye", "bye bye", "see you", "see ya", "peace", "peace out",
    "hide", "close",
}

_stop_event = threading.Event()
_reminder_stop = threading.Event()
_brain_ref = [None]

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
                speaker.speak(f"Reminder: {r['text']}", posture="task")
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
        f"{'s' if len(missed) > 1 else ''}: {names}.",
        posture="task",
    )
    for r in missed:
        memory.advance_reminder(r["id"])


def ask_groq_with_search(user_text, brain):
    reply = brain.think(user_text)
    if _groq_says_unknown(reply):
        ui.set_status("🌐 Browsing web...")
        reply = brain.think_with_search(user_text)
        if _groq_says_unknown(reply):
            reply = "[neutral] I searched the web but couldn't find a reliable answer."
    return reply


def assistant_loop(hud):
    ui.set_status("Loading Whisper...")
    listener = Listener()

    ui.set_status("Loading brain...")
    brain = Brain()
    _brain_ref[0] = brain

    ui.set_status("Loading voice...")
    speaker = Speaker()

    conversation_skill.set_dependencies(speaker, brain)

    is_first_today = relationship.start_session()
    rdata = relationship.load_relationship()
    sessions = int(rdata.get("session_count", 1))
    preferred = rdata.get("preferred_name", "Sir")
    trust = int(rdata.get("trust_level", 1))

    if SHOW_TERMINAL_OUTPUT:
        print(f"[relationship] {relationship.summary_line()}")

    ui.set_status("TRAVIS online")

    # ---- Greeting + optional morning briefing ----
    is_briefing_day = (
        ENABLE_MORNING_BRIEFING
        and is_first_today
        and sessions > 1
    )

    if is_briefing_day:
        # Briefing day — speak the full briefing (includes time-of-day greeting)
        ui.set_status("📰 Preparing briefing...")
        if SHOW_TERMINAL_OUTPUT:
            print("[briefing] generating...")

        briefing_text = None
        try:
            briefing_text = briefing_mod.generate_briefing(preferred)
        except Exception as e:
            print(f"[briefing error] {e}")

        if briefing_text:
            if SHOW_TERMINAL_OUTPUT:
                print(f"[briefing] {briefing_text[:200]}")
            speaker.speak(briefing_text, posture="social")
        else:
            # Briefing failed entirely — fall back to a plain greeting
            from datetime import datetime
            hour = datetime.now().hour
            if 5 <= hour < 12:
                tod = "Good morning"
            elif 12 <= hour < 17:
                tod = "Good afternoon"
            elif 17 <= hour < 21:
                tod = "Good evening"
            else:
                tod = "Working late"
            speaker.speak(f"{tod}, {preferred}.", posture="social")
    else:
        # Normal greeting path (non-briefing)
        if sessions == 1:
            greeting = "TRAVIS system online. How can I assist you?"
        elif trust >= 7:
            greeting = f"Right, {preferred}. What do you need?"
        elif sessions >= 5:
            greeting = f"Right, {preferred}. How can I assist?"
        else:
            greeting = "TRAVIS system online. How can I assist you?"

        speaker.speak(greeting, posture="social")

    # ---- Missed reminders (urgent — always after greeting) ----
    announce_missed(speaker)

    # ---- Recall announcement ----
    try:
        count = brain.exchange_count()
        if count > 0:
            speaker.speak(
                f"I remember our last {count} exchange"
                f"{'s' if count != 1 else ''}.",
                posture="task",
            )
    except Exception:
        pass

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

            relationship.record_message()
            empty_count = 0

            normalized = user_input.lower().strip().strip(" .,!?")
            if normalized in EXIT_WORDS:
                try:
                    import subprocess
                    subprocess.run(
                        "shutdown /a", shell=True,
                        capture_output=True, timeout=5,
                    )
                except Exception:
                    pass
                speaker.speak("Goodbye, Sir. Have a nice day.", posture="social")

                try:
                    hud.root.after(0, hud.root.destroy)
                except Exception:
                    pass
                break

            pref_change = preferences.detect_preference_change(user_input)
            if pref_change:
                if SHOW_TERMINAL_OUTPUT:
                    print(f"[preferences] {pref_change}")
                speaker.speak(pref_change["reply"], posture="social")
                continue

            posture = classify_posture(user_input)
            handled, reply = handle_command(user_input)

            if handled:
                ui.set_status("🔊 Speaking...")
                speaker.speak(reply, posture=posture)
            else:
                ui.set_status("🧠 Thinking...")
                if USE_STREAMING:
                    stream = brain.think_stream(user_input)
                    speaker.speak_stream(stream, posture=posture)
                else:
                    reply = ask_groq_with_search(user_input, brain)
                    ui.set_status("🔊 Speaking...")
                    speaker.speak(reply, posture=posture)

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
    assistant_thread.join(timeout=3)

    try:
        if _brain_ref[0] is not None:
            _brain_ref[0].summarize_session()
    except Exception as e:
        print(f"[summary error] {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Interrupted by user]")
    except Exception as e:
        print(f"[Error] {e}")