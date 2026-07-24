"""Prompt composer text input: plain QPlainTextEdit (native undo/redo,
unlimited length) plus drag-and-drop file attachment.

Dropped files have their text content read and inserted at the cursor,
wrapped in a fenced code block with the filename — the design doc describes
this as "attaches file content into the prompt," not an upload anywhere new.
Binary/undecodable files are skipped with a status signal rather than
inserting garbage.

Also captures keystroke *timing* — never content — for app/core/touch_sense.py
("touch," see that module's docstring for the full design reasoning). Only
two numbers ever leave this widget per keystroke: how long a key was held
(dwell) and the gap since the previous key (latency), tagged with a coarse
structural category (printable/backspace/enter/space/tab/modifier/arrow/
other). No key code and no character is ever stored past the single event
handler that observes it, and neither ever crosses into drain_touch_events()'s
return value — the schema itself has no slot for one.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPlainTextEdit

_MAX_DROP_FILE_BYTES = 500_000  # keep dropped content from blowing up the prompt

_MAX_TOUCH_TIMING_S = 10.0  # mirrors app/core/touch_sense.py's server-side cap
_MODIFIER_KEYS = {
    Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta,
    Qt.Key_CapsLock, Qt.Key_AltGr,
}
_ARROW_KEYS = {Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down}


def _classify_key(event) -> str:
    """Coarse structural category only. event.text() is consulted only to
    test .isprintable() — the character itself is never stored or returned."""
    key = event.key()
    if key in (Qt.Key_Backspace, Qt.Key_Delete):
        return "backspace"
    if key in (Qt.Key_Return, Qt.Key_Enter):
        return "enter"
    if key == Qt.Key_Space:
        return "space"
    if key == Qt.Key_Tab:
        return "tab"
    if key in _MODIFIER_KEYS:
        return "modifier"
    if key in _ARROW_KEYS:
        return "arrow"
    text = event.text()
    if text and text.isprintable():
        return "printable"
    return "other"


def est_tokens(text: str) -> int:
    """Same rough heuristic terminal_client.py/conversation_service.py use
    (len // 4) — small enough to keep local rather than reach into app.core
    from this process."""
    return max(0, len(text) // 4)


class ComposerInput(QPlainTextEdit):
    file_dropped = Signal(str)     # filename, on success
    drop_rejected = Signal(str)    # filename, reason

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._key_down_times: dict[int, float] = {}
        self._last_keydown_ts: float | None = None
        self._touch_events: list[dict] = []

    # ------------------------------------------------------------------
    # Touch (keystroke timing — see module docstring)
    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        self._record_keydown(event)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self._record_keyup(event)
        super().keyReleaseEvent(event)

    def _record_keydown(self, event) -> None:
        if event.isAutoRepeat():
            return
        now = time.monotonic()
        category = _classify_key(event)
        if self._last_keydown_ts is not None:
            latency = now - self._last_keydown_ts
            if 0.0 < latency <= _MAX_TOUCH_TIMING_S:
                self._touch_events.append(
                    {"type": "latency", "value": latency, "category": category}
                )
        self._last_keydown_ts = now
        self._key_down_times[event.key()] = now

    def _record_keyup(self, event) -> None:
        if event.isAutoRepeat():
            return
        now = time.monotonic()
        press_ts = self._key_down_times.pop(event.key(), None)
        if press_ts is None:
            return
        dwell = now - press_ts
        if 0.0 < dwell <= _MAX_TOUCH_TIMING_S:
            self._touch_events.append(
                {"type": "dwell", "value": dwell, "category": _classify_key(event)}
            )

    def drain_touch_events(self) -> list[dict]:
        """Atomically pop and return everything captured since the last
        drain. Called from the main thread by ConversationView's periodic
        flush timer, right before handing the (already-copied) list off to
        a background thread for the actual HTTP report — never includes a
        key code or character, only timing floats and a coarse category."""
        events, self._touch_events = self._touch_events, []
        return events

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            super().dropEvent(event)
            return

        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if not path.is_file():
                continue
            try:
                size = path.stat().st_size
                if size > _MAX_DROP_FILE_BYTES:
                    self.drop_rejected.emit(f"{path.name} (too large: {size} bytes)")
                    continue
                content = path.read_text(encoding="utf-8", errors="strict")
            except (UnicodeDecodeError, OSError) as e:
                self.drop_rejected.emit(f"{path.name} ({e})")
                continue

            cursor = self.textCursor()
            cursor.insertText(f"\n\n[{path.name}]\n```\n{content}\n```\n")
            self.file_dropped.emit(path.name)

        event.acceptProposedAction()
