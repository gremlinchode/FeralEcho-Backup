"""Voice output for Echo Studio responses.

Same library terminal_client.py already uses (pyttsx3), but with its own
dedicated background thread + queue rather than one throwaway thread per
call — pyttsx3 engines aren't safe to drive from two threads at once, and a
queue means a response that finishes speaking late just plays after the one
ahead of it instead of colliding with it.

Deliberately decoupled from the chat send/receive flow: calling speak() only
enqueues text and returns immediately. Nothing about queuing or playing
speech blocks or gates sending the next message — the only thing that gates
sending is an in-flight response generation (ConversationView.is_busy()),
which has no knowledge of this module at all.
"""

from __future__ import annotations

import queue
import threading
from typing import Optional

import pyttsx3


class SpeechOutput:
    def __init__(self, rate: int = 175, volume: float = 1.0):
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        self._engine.setProperty("volume", volume)
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._enabled = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            text = self._queue.get()
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                pass  # a TTS failure should never take down the app

    def speak(self, text: str) -> None:
        """Non-blocking: enqueues text and returns immediately."""
        if not self._enabled or not text.strip():
            return
        self._queue.put(text)

    def stop(self) -> None:
        """Interrupt whatever is currently playing and drop anything queued."""
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass
        try:
            self._engine.stop()
        except Exception:
            pass

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self.stop()

    def is_enabled(self) -> bool:
        return self._enabled


_singleton: Optional[SpeechOutput] = None


def get_speech_output() -> SpeechOutput:
    """Lazily-created, process-wide singleton — one pyttsx3 engine, one
    queue, shared by every view that wants to speak something."""
    global _singleton
    if _singleton is None:
        _singleton = SpeechOutput()
    return _singleton
