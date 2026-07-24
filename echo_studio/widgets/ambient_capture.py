"""
Ambient capture (vision + hearing) — the client half of
app/core/vision_sense.py and app/core/hearing_sense.py.

Runs entirely inside Echo Studio's own process using PySide6.QtMultimedia's
real camera/microphone access. Computes brightness/motion/loudness locally
and discards every raw frame or audio buffer the instant the numbers are
computed — nothing but those numbers (see drain_events()) ever leaves
either class, and neither class has any method that could return a frame,
an image, or an audio buffer even by accident.

Off by default. Only ever started by an explicit, visible user action — see
conversation_view.py's "Let Echo see" / "Let Echo hear" checkboxes. Never
started from a timer, a conversation event, window focus, or any other
inferred signal — the camera/mic indicator light coming on should always
mean a person deliberately turned it on, the same honest signal a video
call gives.

Vision: samples one frame every _VISION_SAMPLE_INTERVAL_S seconds from a
continuous QVideoSink feed (kept running rather than started/stopped per
sample, so the indicator light stays steady rather than flickering).
Converts to grayscale, computes mean brightness and frame-to-frame motion
via numpy, then the frame is gone — never held, never written, never sent.

Hearing: reads raw PCM off the audio device on a timer, computes RMS,
discards the buffer immediately. Never writes audio to disk, never
assembles or transmits a clip.
"""

from __future__ import annotations

import time

import numpy as np
from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import (
    QAudioFormat,
    QAudioSource,
    QCamera,
    QMediaCaptureSession,
    QMediaDevices,
    QVideoSink,
)

_VISION_SAMPLE_INTERVAL_S = 2.0
_HEARING_SAMPLE_INTERVAL_MS = 500
_HEARING_SAMPLE_RATE = 16000


def _qimage_to_gray_array(qimage: QImage) -> np.ndarray:
    """Converts a QImage to a 2D grayscale numpy array, copied out of Qt's
    own buffer before returning — the caller must not hold a reference to
    the QImage/QVideoFrame past this call.

    constBits() returns a plain Python memoryview in this PySide6 version
    (confirmed directly — older bindings return a sip.voidptr needing an
    explicit .setsize() call first; this one already knows its own size),
    so np.frombuffer() can consume it directly."""
    img = qimage.convertToFormat(QImage.Format.Format_Grayscale8)
    width, height, stride = img.width(), img.height(), img.bytesPerLine()
    ptr = img.constBits()
    arr = np.frombuffer(ptr, dtype=np.uint8, count=height * stride).reshape(height, stride)[:, :width]
    return arr.copy()


class VisionCapture(QObject):
    """Owns a QCamera + QVideoSink. Buffers {"type": "brightness"|"motion",
    "value": float} dicts only — never a frame or an image — until drained.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera: "QCamera | None" = None
        self._session: "QMediaCaptureSession | None" = None
        self._sink: "QVideoSink | None" = None
        self._events: list[dict] = []
        self._last_gray = None
        self._last_sample_ts = 0.0
        self._active = False

    def start(self) -> bool:
        if self._active:
            return True
        try:
            device = QMediaDevices.defaultVideoInput()
            if device.isNull():
                return False
            self._camera = QCamera(device)
            self._sink = QVideoSink()
            self._session = QMediaCaptureSession()
            self._session.setCamera(self._camera)
            self._session.setVideoSink(self._sink)
            self._sink.videoFrameChanged.connect(self._on_frame)
            self._camera.start()
            self._active = True
            return True
        except Exception:
            self.stop()
            return False

    def stop(self) -> None:
        self._active = False
        try:
            if self._camera:
                self._camera.stop()
        except Exception:
            pass
        self._camera = None
        self._session = None
        self._sink = None
        self._last_gray = None

    def _on_frame(self, frame) -> None:
        if not self._active:
            return
        now = time.monotonic()
        if now - self._last_sample_ts < _VISION_SAMPLE_INTERVAL_S:
            return
        self._last_sample_ts = now
        try:
            image = frame.toImage()
            if image.isNull():
                return
            gray = _qimage_to_gray_array(image)
            brightness = float(gray.mean()) / 255.0
            self._events.append({"type": "brightness", "value": brightness})
            if self._last_gray is not None and self._last_gray.shape == gray.shape:
                diff = np.abs(gray.astype(np.int16) - self._last_gray.astype(np.int16))
                motion = float(diff.mean()) / 255.0
                self._events.append({"type": "motion", "value": motion})
            self._last_gray = gray
        except Exception:
            pass  # one bad frame is skipped, never crashes capture

    def drain_events(self) -> list[dict]:
        """Atomically pop and return everything captured since the last
        drain. Never includes a frame or an image — only the two numeric
        readings computed in _on_frame()."""
        events, self._events = self._events, []
        return events


class HearingCapture(QObject):
    """Owns a QAudioSource in pull mode. Buffers {"type": "loudness",
    "value": float} dicts only — never raw audio — until drained."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._audio_source: "QAudioSource | None" = None
        self._audio_io = None
        self._timer: "QTimer | None" = None
        self._events: list[dict] = []
        self._active = False

    def start(self) -> bool:
        if self._active:
            return True
        try:
            device = QMediaDevices.defaultAudioInput()
            if device.isNull():
                return False
            fmt = QAudioFormat()
            fmt.setSampleRate(_HEARING_SAMPLE_RATE)
            fmt.setChannelCount(1)
            fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
            self._audio_source = QAudioSource(device, fmt)
            self._audio_io = self._audio_source.start()
            if self._audio_io is None:
                self.stop()
                return False
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._sample)
            self._timer.start(_HEARING_SAMPLE_INTERVAL_MS)
            self._active = True
            return True
        except Exception:
            self.stop()
            return False

    def stop(self) -> None:
        self._active = False
        try:
            if self._timer:
                self._timer.stop()
        except Exception:
            pass
        try:
            if self._audio_source:
                self._audio_source.stop()
        except Exception:
            pass
        self._audio_source = None
        self._audio_io = None
        self._timer = None

    def _sample(self) -> None:
        if not self._active or self._audio_io is None:
            return
        try:
            raw = bytes(self._audio_io.readAll())
            if not raw:
                return
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if samples.size == 0:
                return
            rms = float(np.sqrt(np.mean(samples ** 2)))
            self._events.append({"type": "loudness", "value": min(rms, 1.0)})
        except Exception:
            pass  # one bad read is skipped, never crashes capture

    def drain_events(self) -> list[dict]:
        """Atomically pop and return everything captured since the last
        drain. Never includes an audio buffer — only the RMS readings
        computed in _sample()."""
        events, self._events = self._events, []
        return events
