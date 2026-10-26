import queue
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import (
    INPUT_MODE, PUSH_TO_TALK_HOTKEY, SILENCE_TIMEOUT,
)
from core import ui

WHISPER_MODEL_SIZE = "small"

try:
    import keyboard
    _HAS_KEYBOARD = True
except ImportError:
    _HAS_KEYBOARD = False

_INITIAL_PROMPT = (
    "Short spoken commands to a personal assistant: "
    "what time is it, what is today's date, take a screenshot, "
    "open chrome, open calculator, open notepad, volume up, mute, "
    "tell me about science, astronomy, history. "
    "Common commands: what's my password, what's my birthday, "
    "remember that, remind me to, what do you remember about, "
    "open notepad, close chrome, tell me about."
)


class Listener:
    def __init__(self):
        self.whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE, device="cpu", compute_type="int8"
        )
        self.audio_queue = queue.Queue()

        self.push_to_talk = (INPUT_MODE == "ptt" and _HAS_KEYBOARD)
        if INPUT_MODE == "ptt" and not _HAS_KEYBOARD:
            ui.set_status("⚠ keyboard not installed — using VAD")

        try:
            silence = np.zeros(1600, dtype=np.float32)
            list(self.whisper_model.transcribe(silence, language="en"))
        except Exception:
            pass

    def _callback(self, indata, frames, time_info, status):
        if status:
            ui.set_status(f"⚠ audio: {status}")
        self.audio_queue.put(indata.copy())

    def _drain(self):
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def _transcribe(self, audio_chunks):
        if not audio_chunks:
            return ""
        audio = np.concatenate(audio_chunks, axis=0).flatten().astype(np.float32)
        segments, info = self.whisper_model.transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=True,
            initial_prompt=_INITIAL_PROMPT,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        if text:
            ui.set_you(text)
        return text

    def listen(self, silence_timeout=SILENCE_TIMEOUT):
        if self.push_to_talk:
            return self._listen_ptt()
        return self._listen_vad(silence_timeout)

    def _listen_ptt(self):
        self._drain()
        while not keyboard.is_pressed(PUSH_TO_TALK_HOTKEY):
            time.sleep(0.05)
        time.sleep(0.05)

        ui.set_status("🔴 Recording...")
        audio_chunks = []

        with sd.InputStream(
            samplerate=16000, blocksize=4000, dtype="float32",
            channels=1, callback=self._callback
        ):
            while keyboard.is_pressed(PUSH_TO_TALK_HOTKEY):
                try:
                    audio_chunks.append(self.audio_queue.get(timeout=0.05))
                except queue.Empty:
                    pass

        time.sleep(0.15)
        while not self.audio_queue.empty():
            try:
                audio_chunks.append(self.audio_queue.get_nowait())
            except queue.Empty:
                break

        ui.set_status("⏹️  Processing...")
        return self._transcribe(audio_chunks)

    def _listen_vad(self, silence_timeout):
        self._drain()
        ui.set_status("🎤 Listening...")
        audio_chunks = []
        last_speech_time = time.time()
        noise_floor = None

        with sd.InputStream(
            samplerate=16000, blocksize=4000, dtype="float32",
            channels=1, callback=self._callback
        ):
            while True:
                chunk = self.audio_queue.get()
                audio_chunks.append(chunk)
                rms = float(np.sqrt(np.mean(chunk ** 2)))

                if noise_floor is None:
                    noise_floor = rms
                else:
                    alpha = 0.3 if rms < noise_floor else 0.02
                    noise_floor = alpha * rms + (1 - alpha) * noise_floor

                if rms > max(noise_floor * 3.5, 0.005):
                    last_speech_time = time.time()

                if time.time() - last_speech_time > silence_timeout:
                    break

        ui.set_status("⏹️  Processing...")
        return self._transcribe(audio_chunks)