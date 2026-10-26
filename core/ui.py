import math
import queue
import tkinter as tk

from config import SHOW_TERMINAL_OUTPUT

_hud = None

# State → orb color (RGB 0..1)
_STATE_COLORS = {
    "idle":      (0.40, 0.40, 0.50),
    "listening": (0.00, 0.90, 1.00),
    "thinking":  (1.00, 0.75, 0.10),
    "speaking":  (0.30, 0.75, 1.00),
    "error":     (1.00, 0.30, 0.30),
}


class HUD:
    def __init__(self):
        self.queue = queue.Queue()

        self.root = tk.Tk()
        self.root.title("T.R.A.V.I.S")
        self.root.geometry("520x680+50+50")
        self.root.configure(bg="#050810")
        self.root.attributes("-topmost", True)

        # ---------- Animated orb canvas ----------
        self.orb_canvas = tk.Canvas(
            self.root, width=520, height=230,
            bg="#050810", highlightthickness=0,
        )
        self.orb_canvas.pack(fill="x", pady=(6, 0))

        # Status label
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Consolas", 11, "bold"),
            bg="#050810", fg="#8892a0",
        )
        self.status_label.pack(pady=(0, 6))

        # ---------- Chat log ----------
        self.chat_frame = tk.Frame(self.root, bg="#050810")
        self.chat_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.chat_text = tk.Text(
            self.chat_frame,
            font=("Segoe UI", 10),
            bg="#0a0f1c", fg="#c8d0e0",
            wrap="word", relief="flat", borderwidth=0,
            padx=14, pady=12,
            state="disabled", cursor="arrow",
            spacing1=2, spacing3=10,
        )
        scrollbar = tk.Scrollbar(
            self.chat_frame, command=self.chat_text.yview,
            bg="#1a2030", troughcolor="#0a0f1c",
            activebackground="#2a3040", width=10,
        )
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.chat_text.pack(side="left", fill="both", expand=True)

        self.chat_text.tag_configure(
            "you_tag",
            foreground="#8892a0",
            font=("Segoe UI", 9, "bold"),
            spacing1=10,
        )
        self.chat_text.tag_configure(
            "you_body",
            foreground="#c8d0e0",
            font=("Segoe UI", 10),
            lmargin1=8, lmargin2=8,
            spacing3=4,
        )
        self.chat_text.tag_configure(
            "travis_tag",
            foreground="#00e5ff",
            font=("Segoe UI", 9, "bold"),
            spacing1=6,
        )
        self.chat_text.tag_configure(
            "travis_body",
            foreground="#4fc3f7",
            font=("Segoe UI", 10),
            lmargin1=8, lmargin2=8,
            spacing3=10,
        )

        # ---------- Animation state ----------
        self.state = "idle"
        self.pulse_phase = 0.0
        self.orb_rgb = [0.4, 0.4, 0.5]

        self._travis_stream_start = None

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll()
        self._animate()

    # ---------- Queue polling ----------
    def _poll(self):
        try:
            while True:
                fn = self.queue.get_nowait()
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        try:
            self.root.after(50, self._poll)
        except tk.TclError:
            pass

    # ---------- Animation loop ----------
    def _animate(self):
        try:
            self._draw_orb()
            self.root.after(16, self._animate)   # ~60 FPS
        except tk.TclError:
            pass

    def _draw_orb(self):
        c = self.orb_canvas
        c.delete("all")

        cx, cy = 260, 105
        self.pulse_phase += 0.08

        # Smooth color transitions
        target = _STATE_COLORS.get(self.state, (0.0, 0.9, 1.0))
        for i in range(3):
            self.orb_rgb[i] += (target[i] - self.orb_rgb[i]) * 0.15

        r, g, b = (int(v * 255) for v in self.orb_rgb)
        color = f"#{r:02x}{g:02x}{b:02x}"
        darker = f"#{int(r*0.5):02x}{int(g*0.5):02x}{int(b*0.5):02x}"
        glow = f"#{int(r*0.18):02x}{int(g*0.18):02x}{int(b*0.18):02x}"

        # Radius per state
        if self.state == "idle":
            base_r = 28 + 2 * math.sin(self.pulse_phase)
        elif self.state == "listening":
            base_r = 42 + 6 * math.sin(self.pulse_phase * 1.5)
        elif self.state == "thinking":
            base_r = 36 + 3 * math.sin(self.pulse_phase * 2)
        elif self.state == "speaking":
            base_r = 44 + 7 * math.sin(self.pulse_phase * 2.5)
        elif self.state == "error":
            base_r = 40
        else:
            base_r = 36

        # Glow
        for i in range(4, 0, -1):
            gr = base_r + i * 10
            c.create_oval(cx - gr, cy - gr, cx + gr, cy + gr, fill=glow, outline="")

        # Main orb
        c.create_oval(cx - base_r, cy - base_r, cx + base_r, cy + base_r,
                      fill=color, outline=darker, width=2)

        # Highlight
        hr = base_r * 0.35
        off = base_r * 0.30
        c.create_oval(cx - off - hr, cy - off - hr, cx - off + hr, cy - off + hr,
                      fill=f"#{min(255,r+70):02x}{min(255,g+70):02x}{min(255,b+70):02x}",
                      outline="")

        # State-specific overlays
        if self.state == "thinking":
            arc_r = base_r + 18
            angle = (self.pulse_phase * 60) % 360
            c.create_arc(cx - arc_r, cy - arc_r, cx + arc_r, cy + arc_r,
                         start=angle, extent=100,
                         style="arc", outline=color, width=3)

        elif self.state == "listening":
            bars = 28
            spacing = 8
            total_w = bars * spacing
            start_x = cx - total_w / 2
            base_y = cy + 72
            for i in range(bars):
                amp = abs(math.sin(self.pulse_phase * 2 + i * 0.5)) * 14 + 3
                x = start_x + i * spacing
                c.create_rectangle(x, base_y - amp, x + 4, base_y + amp,
                                   fill=color, outline="")

        elif self.state == "speaking":
            # Concentric "voice rings"
            for i in range(3):
                ring_r = base_r + 12 + i * 14 + (self.pulse_phase * 4) % 14
                ring_color = f"#{int(r*0.3):02x}{int(g*0.3):02x}{int(b*0.3):02x}"
                c.create_oval(cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r,
                              outline=ring_color, width=1)

    # ---------- Chat helpers ----------
    def _scroll_if_at_bottom(self):
        try:
            _, y_end = self.chat_text.yview()
            if y_end > 0.9:
                self.chat_text.see("end")
        except Exception:
            pass

    def _on_you(self, text):
        self._travis_stream_start = None

        self.chat_text.configure(state="normal")
        if self.chat_text.index("end-1c") != "1.0":
            self.chat_text.insert("end", "\n")
        self.chat_text.insert("end", "You\n", "you_tag")
        self.chat_text.insert("end", f"{text}\n", "you_body")
        self.chat_text.configure(state="disabled")
        self._scroll_if_at_bottom()

    def _on_travis(self, text, streaming):
        self.chat_text.configure(state="normal")

        if streaming and self._travis_stream_start is not None:
            try:
                self.chat_text.delete(self._travis_stream_start, "end")
            except Exception:
                pass
        else:
            if self.chat_text.index("end-1c") != "1.0":
                self.chat_text.insert("end", "\n")
            self._travis_stream_start = None

        start = self.chat_text.index("end-1c")
        self.chat_text.insert("end", "TRAVIS\n", "travis_tag")
        self.chat_text.insert("end", f"{text}\n", "travis_body")

        if streaming:
            self._travis_stream_start = start

        self.chat_text.configure(state="disabled")
        self._scroll_if_at_bottom()

    def _on_status(self, text):
        self.status_var.set(text)
        text_lower = text.lower()
        if "record" in text_lower or "listening" in text_lower:
            self.state = "listening"
        elif "processing" in text_lower or "thinking" in text_lower:
            self.state = "thinking"
        elif "speaking" in text_lower:
            self.state = "speaking"
        elif "error" in text_lower:
            self.state = "error"
        else:
            self.state = "idle"

    def _on_close(self):
        global _hud
        _hud = None
        try:
            self.root.destroy()
        except Exception:
            pass

    # ---------- Thread-safe API ----------
    def set_status(self, text):
        self.queue.put(lambda: self._on_status(text))

    def set_you(self, text):
        self.queue.put(lambda: self._on_you(text))

    def set_travis(self, text, streaming=False):
        self.queue.put(lambda: self._on_travis(text, streaming))

    def run(self):
        self.root.mainloop()


# ---------- Module-level API ----------
def init_hud():
    global _hud
    _hud = HUD()
    return _hud


def set_status(text):
    if SHOW_TERMINAL_OUTPUT:
        print(text)
    if _hud:
        _hud.set_status(text)


def set_you(text):
    if SHOW_TERMINAL_OUTPUT:
        print(f"You: {text}")
    if _hud:
        _hud.set_you(text)


def set_travis(text, streaming=False):
    if SHOW_TERMINAL_OUTPUT:
        print(f"TRAVIS: {text}")
    if _hud:
        _hud.set_travis(text, streaming=streaming)