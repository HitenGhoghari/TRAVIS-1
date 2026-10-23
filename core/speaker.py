import re
import queue
import threading
import sounddevice as sd
from kokoro import KPipeline
from config import KOKORO_LANG, KOKORO_VOICE, KOKORO_SPEED


def clean_for_speech(text: str) -> str:
    """Strip markdown, bullets, and newlines so Kokoro speaks smoothly."""
    text = re.sub(r"[*#`_>]", "", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class Speaker:
    def __init__(self):
        self.pipeline = KPipeline(lang_code=KOKORO_LANG, repo_id="hexgrad/Kokoro-82M")

        # Pre-warm — synthesis is lazy, so the first real call is always slow.
        try:
            list(self.pipeline(
                "Ready.", voice=KOKORO_VOICE, speed=KOKORO_SPEED,
                split_pattern=None,
            ))
        except Exception:
            pass

    def speak(self, text: str):
        text = clean_for_speech(text)
        print(f"TRAVIS: {text}")

        # Buffer holds pre-synthesized audio chunks
        audio_queue: "queue.Queue" = queue.Queue(maxsize=4)

        def producer():
            """Synthesize each sentence and push it to the queue."""
            try:
                for _, _, audio in self.pipeline(
                    text,
                    voice=KOKORO_VOICE,
                    speed=KOKORO_SPEED,
                    split_pattern=r"(?<=[.!?])\s+",   # sentence-level
                ):
                    audio_queue.put(audio)
            finally:
                audio_queue.put(None)  # sentinel: synthesis done

        thread = threading.Thread(target=producer, daemon=True)
        thread.start()

        # Main thread: play chunks as they arrive
        first = True
        while True:
            audio = audio_queue.get()
            if audio is None:
                break

            # On the very first chunk, add a tiny fade-in so there's no
            # click when audio starts (optional, harmless).
            if first:
                first = False

            sd.play(audio, samplerate=24000)
            sd.wait()   # block only while playing; producer keeps working