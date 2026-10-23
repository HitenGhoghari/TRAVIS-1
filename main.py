import os
import time
import threading

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import warnings
warnings.filterwarnings("ignore")

from core.listener import Listener
from core.brain import Brain
from core.speaker import Speaker
from core import memory
from config import LOG_DIR
from commands.router import handle as handle_command

os.makedirs(LOG_DIR, exist_ok=True)

EXIT_WORDS = {"exit", "stop", "goodbye", "quit", "shut down", "shutdown"}

_reminder_stop = threading.Event()


def reminder_worker(speaker):
    while not _reminder_stop.is_set():
        try:
            due = memory.get_due_reminders()
            for r in due:
                time.sleep(1)
                speaker.speak(f"Reminder: {r['text']}")
                memory.mark_fired(r["id"])
        except Exception as e:
            print(f"[Reminder error] {e}")
        _reminder_stop.wait(30)


def main():
    print("=" * 50)
    print("  T.R.A.V.I.S  -  Initializing...")
    print("=" * 50)

    listener = Listener()
    brain = Brain()
    speaker = Speaker()

    speaker.speak("TRAVIS system online. How can I assist you?")

    reminder_thread = threading.Thread(
        target=reminder_worker, args=(speaker,), daemon=True
    )
    reminder_thread.start()

    empty_count = 0

    try:
        while True:
            if empty_count == 0 and not listener.push_to_talk:
                print("🎤 Listening...")

            user_input = listener.listen()

            if not user_input:
                if listener.push_to_talk:
                    continue  # no backoff — you released the key without speaking
                empty_count += 1
                time.sleep(min(0.5 * empty_count, 5.0))
                continue

            empty_count = 0

            if any(word in user_input.lower() for word in EXIT_WORDS):
                speaker.speak("Goodbye, Sir. Have a nice day.")
                break

            handled, reply = handle_command(user_input)
            if not handled:
                reply = brain.think(user_input)

            speaker.speak(reply)
    finally:
        _reminder_stop.set()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Interrupted by user]")
    except Exception as e:
        print(f"[Error] {e}")