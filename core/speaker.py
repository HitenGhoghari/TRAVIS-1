import queue
import re
import threading

import sounddevice as sd
from kokoro import KPipeline

from config import KOKORO_LANG, KOKORO_VOICE, KOKORO_SPEED
from core import ui


def clean_for_speech(text: str) -> str:
    text = re.sub(r"[*#`_>]", "", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class Speaker:
    def __init__(self):
        self.pipeline = KPipeline(lang_code=KOKORO_LANG)
        self.last_spoken = ""   # ← new: tracks the most recent spoken text
        try:
            list(self.pipeline(
                "Ready.", voice=KOKORO_VOICE, speed=KOKORO_SPEED,
                split_pattern=None,
            ))
        except Exception:
            pass

    def _play_audio(self, text: str):
        audio_queue = queue.Queue(maxsize=4)

        def producer():
            try:
                for _, _, audio in self.pipeline(
                    text,
                    voice=KOKORO_VOICE,
                    speed=KOKORO_SPEED,
                    split_pattern=r"(?<=[.!?])\s+",
                ):
                    audio_queue.put(audio)
            finally:
                audio_queue.put(None)

        thread = threading.Thread(target=producer, daemon=True)
        thread.start()

        while True:
            audio = audio_queue.get()
            if audio is None:
                break
            sd.play(audio, samplerate=24000)
            sd.wait()

    def speak(self, text: str):
        text = clean_for_speech(text)
        self.last_spoken = text        # ← update before playing
        ui.set_travis(text, streaming=False)
        self._play_audio(text)

    def speak_stream(self, text_iterator):
        buffer = ""
        full_text = ""

        for chunk in text_iterator:
            buffer += chunk
            while True:
                positions = [buffer.find(p) for p in ".!?" if p in buffer]
                if not positions:
                    break
                idx = min(positions)
                sentence = buffer[: idx + 1].strip()
                buffer = buffer[idx + 1:].lstrip()
                if sentence:
                    full_text = (full_text + " " + sentence).strip()
                    ui.set_travis(full_text, streaming=True)
                    self._play_audio(sentence)

        if buffer.strip():
            full_text = (full_text + " " + buffer.strip()).strip()
            ui.set_travis(full_text, streaming=True)
            self._play_audio(buffer.strip())

        if full_text:
            self.last_spoken = full_text   # ← update once for the whole stream