import os
import re
import queue
import threading
import numpy as np
import sounddevice as sd

from config import (
    VOICE_ENGINE,
    KOKORO_LANG,
    KOKORO_VOICE,
    KOKORO_SAFETY_VOICE,
    KOKORO_SPEED,
    PIPER_VOICE,
    PIPER_SAFETY_VOICE,
    PIPER_LENGTH_SCALE,
    EMOTION_SPEED,
    SPAN_PAUSE_SECONDS,
    BASE_DIR,
)
from core import ui
from core.emotions import parse_spans, strip_tags, normalize_emotion

KOKORO_RATE = 24000
PIPER_RATE = 22050


def clean_for_speech(text: str) -> str:
    text = re.sub(r"[*#`_>]", "", text)

    # Normalize punctuation that Kokoro's phonemizer chokes on.
    # Semicolon → period: creates a sentence break, gets its own emotion tag,
    # and Kokoro synthesizes each sentence cleanly.
    text = text.replace(";", ".")

    # Em/en dash → comma (safer pause, no phonemizer crash)
    text = text.replace("—", ", ")
    text = text.replace("–", ", ")

    # Ellipsis → period
    text = text.replace("…", ".")

    # Curly quotes → straight (avoids encoding edge cases)
    text = text.replace(""", '"').replace(""", '"')
    text = text.replace("'", "'").replace("'", "'")

    # Non-breaking hyphen → regular hyphen
    text = text.replace("‑", "-").replace("–", "-").replace("—", "-")

    # Strip unicode space variants (Groq occasionally emits these)
    text = text.replace("\u202f", " ")   # narrow no-break space
    text = text.replace("\u00a0", " ")   # non-breaking space
    text = text.replace("\u2009", " ")   # thin space

    # Clean up double punctuation from replacements
    text = re.sub(r"\.\s*\.", ".", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s+([.,!?])", r"\1", text)   # no space before punctuation
    text = re.sub(r"([.,!?])([^\s.,!?])", r"\1 \2", text)  # space after punctuation

    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _resample(audio, from_rate, to_rate):
    if from_rate == to_rate:
        return audio
    from scipy.signal import resample_poly
    from math import gcd
    g = gcd(int(from_rate), int(to_rate))
    up = int(to_rate) // g
    down = int(from_rate) // g
    return resample_poly(audio, up, down).astype(np.float32)


class Speaker:
    def __init__(self):
        self.engine = "piper"
        self.piper_voice = None
        self.piper_safety = None
        self.kokoro_pipe = None
        self.kokoro_voice = None
        self.kokoro_safety = None
        self.current_posture = "task"
        self.last_spoken = ""
        self._audio_debug_printed = False

        try:
            self.output_rate = int(
                sd.query_devices(sd.default.device[1], "output")["default_samplerate"]
            )
        except Exception:
            self.output_rate = 44100

        print(f"[Speaker] Device native rate: {self.output_rate} Hz")

        self.stream = sd.OutputStream(
            samplerate=self.output_rate,
            channels=1,
            dtype="float32",
            blocksize=4096,
            latency="high",
        )
        self.stream.start()

        if VOICE_ENGINE == "kokoro":
            self._init_kokoro()
        else:
            self._init_piper()

        self._warm_up()

    # ---------- Kokoro ----------
    def _init_kokoro(self):
        from kokoro import KPipeline

        print(f"[Speaker] Loading Kokoro ({KOKORO_LANG}, {KOKORO_VOICE})...")
        self.kokoro_pipe = KPipeline(lang_code=KOKORO_LANG)
        self.kokoro_voice = KOKORO_VOICE
        self.kokoro_safety = KOKORO_SAFETY_VOICE or KOKORO_VOICE
        self.engine = "kokoro"
        print(f"[Speaker] Kokoro ready ({KOKORO_RATE} Hz)")

    # ---------- Piper ----------
    def _init_piper(self):
        from piper.voice import PiperVoice

        def load(name, required=False):
            path = os.path.join(BASE_DIR, "piper_models", f"{name}.onnx")
            if not os.path.exists(path):
                if required:
                    raise FileNotFoundError(f"Piper voice missing: {path}")
                return None
            print(f"[Speaker] Loading Piper voice: {path}")
            return PiperVoice.load(path)

        self.piper_voice = load(PIPER_VOICE, required=True)
        self.piper_safety = load(PIPER_SAFETY_VOICE, required=False) or self.piper_voice
        self.engine = "piper"
        self.piper_rate = self.piper_voice.config.sample_rate
        print(f"[Speaker] Piper ready ({self.piper_rate} Hz)")

    def _warm_up(self):
        try:
            if self.engine == "kokoro":
                list(self.kokoro_pipe(
                    "Ready.",
                    voice=self.kokoro_voice,
                    speed=KOKORO_SPEED,
                    split_pattern=None,
                ))
            else:
                from piper.voice import SynthesisConfig
                for _ in self.piper_voice.synthesize(
                    "Ready.", syn_config=SynthesisConfig()
                ):
                    pass
        except Exception as e:
            print(f"[warm-up error] {e}")

    # ---------- Playback ----------
    def _play_silence(self, seconds: float):
        samples = int(self.output_rate * seconds)
        if samples > 0:
            try:
                self.stream.write(
                    np.zeros((samples, 1), dtype=np.float32)
                )
            except Exception as e:
                print(f"[silence error] {e}")

    def _play_audio(self, audio, source_rate):
        if len(audio) == 0:
            return

        rms_val = float(np.sqrt(np.mean(audio ** 2)))

        if not self._audio_debug_printed:
            print(
                f"[audio debug] engine={self.engine} src={source_rate} "
                f"dev={self.output_rate} len={len(audio)} "
                f"min={audio.min():.4f} max={audio.max():.4f} "
                f"rms={rms_val:.4f} "
                f"posture={self.current_posture}"
            )
            self._audio_debug_printed = True

        # Warn if a chunk is essentially silent — indicates phonemizer failure
        if rms_val < 0.005 and len(audio) > 2000:
            print(
                f"[audio warning] near-silent chunk ({len(audio)} samples, "
                f"rms={rms_val:.6f}) — phonemizer likely failed"
            )

        audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
        peak = float(np.max(np.abs(audio)))
        if peak > 1.0:
            audio = audio / peak

        if self.output_rate != source_rate:
            audio = _resample(audio, source_rate, self.output_rate)

        try:
            if audio.ndim == 1:
                audio = audio.reshape(-1, 1)
            self.stream.write(audio)
        except Exception as e:
            print(f"[stream write error] {e}")

    # ---------- Synthesis ----------
    def _play_span(self, text: str, emotion: str):
        if not text.strip():
            return

        emotion = normalize_emotion(emotion)
        speed = EMOTION_SPEED.get(emotion, 1.0)

        # ---------- Kokoro: producer/consumer to eliminate gaps ----------
        if self.engine == "kokoro":
            voice = (
                self.kokoro_safety
                if self.current_posture == "safety"
                else self.kokoro_voice
            )

            audio_queue = queue.Queue(maxsize=6)
            _SENTINEL = object()

            def producer():
                try:
                    gen = self.kokoro_pipe(
                        text,
                        voice=voice,
                        speed=speed * KOKORO_SPEED,
                        split_pattern=r"(?<=[.!?])\s+",
                    )
                    for _, _, audio in gen:
                        if hasattr(audio, "detach"):
                            audio = audio.detach().cpu().numpy()
                        audio_queue.put(
                            np.asarray(audio, dtype=np.float32).reshape(-1)
                        )
                except Exception as e:
                    print(f"[kokoro synth error] {e}")
                finally:
                    audio_queue.put(_SENTINEL)

            thread = threading.Thread(target=producer, daemon=True)
            thread.start()

            while True:
                audio = audio_queue.get()
                if audio is _SENTINEL:
                    break
                self._play_audio(audio, KOKORO_RATE)
            return

        # ---------- Piper path (unchanged) ----------
        from piper.voice import SynthesisConfig

        voice = (
            self.piper_safety
            if self.current_posture == "safety"
            else self.piper_voice
        )
        length_scale = (1.0 / speed) * PIPER_LENGTH_SCALE
        syn_config = SynthesisConfig(length_scale=length_scale)

        chunks = []
        for audio_chunk in voice.synthesize(text, syn_config=syn_config):
            chunks.append(
                np.frombuffer(audio_chunk.audio_int16_bytes, dtype=np.int16)
            )

        if chunks:
            audio = np.concatenate(chunks).astype(np.float32) / 32768.0
            self._play_audio(audio, PIPER_RATE)

    # ---------- Public ----------
    def speak(self, text: str, emotion: str = None, posture: str = None):
        if posture:
            self.current_posture = posture

        text = clean_for_speech(text)
        self.last_spoken = text
        ui.set_travis(strip_tags(text), streaming=False)

        spans = parse_spans(text)
        if not spans:
            spans = [(emotion or "neutral", strip_tags(text))]

        for i, (emo, span_text) in enumerate(spans):
            if i > 0:
                self._play_silence(SPAN_PAUSE_SECONDS)
            if emotion and len(spans) == 1:
                emo = emotion
            self._play_span(span_text, emo)

    def speak_stream(self, text_iterator, posture: str = None):
        if posture:
            self.current_posture = posture

        buffer = full_raw = full_display = ""
        first_span = True

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
                    full_raw = (full_raw + " " + sentence).strip()
                    full_display = (full_display + " " + strip_tags(sentence)).strip()
                    ui.set_travis(full_display, streaming=True)
                    for emo, span_text in parse_spans(sentence):
                        if not first_span:
                            self._play_silence(SPAN_PAUSE_SECONDS)
                        first_span = False
                        self._play_span(span_text, emo)

        if buffer.strip():
            full_raw = (full_raw + " " + buffer.strip()).strip()
            full_display = (full_display + " " + strip_tags(buffer)).strip()
            ui.set_travis(full_display, streaming=True)
            for emo, span_text in parse_spans(buffer):
                if not first_span:
                    self._play_silence(SPAN_PAUSE_SECONDS)
                first_span = False
                self._play_span(span_text, emo)

        if full_raw:
            self.last_spoken = full_raw

    def close(self):
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass