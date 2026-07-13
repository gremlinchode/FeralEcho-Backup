"""Prompt composer text input: plain QPlainTextEdit (native undo/redo,
unlimited length) plus drag-and-drop file attachment.

Dropped files have their text content read and inserted at the cursor,
wrapped in a fenced code block with the filename — the design doc describes
this as "attaches file content into the prompt," not an upload anywhere new.
Binary/undecodable files are skipped with a status signal rather than
inserting garbage.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPlainTextEdit

_MAX_DROP_FILE_BYTES = 500_000  # keep dropped content from blowing up the prompt


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
